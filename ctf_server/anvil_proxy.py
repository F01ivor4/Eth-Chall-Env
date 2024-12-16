import json
import logging
from ast import Dict, List
from contextlib import asynccontextmanager
from typing import Any, Optional

import aiohttp
import asyncio
from fastapi import FastAPI, Request, WebSocket
import websockets
import os


ALLOWED_NAMESPACES = ["web3", "eth", "net"]
DISALLOWED_METHODS = [
    "eth_sign",
    "eth_signTransaction",
    "eth_signTypedData",
    "eth_signTypedData_v3",
    "eth_signTypedData_v4",
    "eth_sendTransaction",
    "eth_sendUnsignedTransaction",
]

ANVIL_IP = os.getenv("ANVIL_IP", "127.0.0.1")
ANVIL_PORT = os.getenv("ANVIL_PORT", "18545")
anvil_instance = {
    "ip": ANVIL_IP,
    "port": ANVIL_PORT,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global session
    session = aiohttp.ClientSession()

    yield

    await session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return "rpc proxy running"


def jsonrpc_fail(id: Any, code: int, message: str) -> Dict:
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def validate_request(request: Any) -> Optional[Dict]:
    if not isinstance(request, dict):
        return jsonrpc_fail(None, -32600, "expected json object")

    request_id = request.get("id")
    request_method = request.get("method")

    if request_id is None:
        return jsonrpc_fail(None, -32600, "invalid jsonrpc id")

    if not isinstance(request_method, str):
        return jsonrpc_fail(request["id"], -32600, "invalid jsonrpc method")

    if (
        request_method.split("_")[0] not in ALLOWED_NAMESPACES
        or request_method in DISALLOWED_METHODS
    ):
        return jsonrpc_fail(request["id"], -32600, "forbidden jsonrpc method")

    return None


async def proxy_request(
    request_id: Optional[str], body: Any
) -> Optional[Any]:
    instance_host = f"http://{anvil_instance['ip']}:{anvil_instance['port']}"

    try:
        async with session.post(instance_host, json=body) as resp:
            return await resp.json()
    except Exception as e:
        logging.error(
            "failed to proxy anvil request to ", exc_info=e
        )
        return jsonrpc_fail(request_id, -32602, str(e))


@app.post("/")
async def rpc(request: Request):
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return jsonrpc_fail(None, -32600, "expected json body")

    # special handling for batch requests
    if isinstance(body, list):
        responses = []
        for idx, req in enumerate(body):
            validation_error = validate_request(req)
            responses.append(validation_error)

            if validation_error is not None:
                # neuter the request
                body[idx] = {
                    "jsonrpc": "2.0",
                    "id": idx,
                    "method": "web3_clientVersion",
                }

        upstream_responses = await proxy_request(None, body)

        for idx in range(len(responses)):
            if responses[idx] is None:
                if isinstance(upstream_responses, List):
                    responses[idx] = upstream_responses[idx]
                else:
                    responses[idx] = upstream_responses

        return responses

    validation_resp = validate_request(body)
    if validation_resp is not None:
        return validation_resp

    return await proxy_request(body["id"], body)

async def forward_message(client_to_remote: bool, client_ws: WebSocket, remote_ws: websockets):
    if client_to_remote:
        async for message in client_ws.iter_text():
            try:
                json_msg = json.loads(message)
            except json.JSONDecodeError:
                await client_ws.send_json(jsonrpc_fail(None, -32600, "expected json body"))
                continue

            validation = validate_request(json_msg)
            if validation is not None:
                await client_ws.send_json(validation)
            else:
                await remote_ws.send(json.dumps(json_msg))
    else:
        async for message in remote_ws:
            await client_ws.send_text(message)

@app.websocket("/")
async def ws_rpc(client_ws: WebSocket):

    instance_host = f"ws://{anvil_instance['ip']}:{anvil_instance['port']}"

    async with websockets.connect(instance_host) as remote_ws:
        await client_ws.accept()
        task_a = asyncio.create_task(forward_message(True, client_ws, remote_ws))
        task_b = asyncio.create_task(forward_message(False, client_ws, remote_ws))

        try:
            await asyncio.wait([task_a, task_b], return_when=asyncio.FIRST_COMPLETED)
            task_a.cancel()
            task_b.cancel()
        except:
            pass
