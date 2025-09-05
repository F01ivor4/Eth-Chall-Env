import json
import logging
from typing import Dict, List
from contextlib import asynccontextmanager
from typing import Any, Optional
import subprocess
import traceback

import aiohttp
import asyncio
from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
import websockets
import os
from eth_account.hdaccount import generate_mnemonic
from eth_abi import abi

# Import required modules for challenge functionality
from ctf_launchers.types import (
    LaunchAnvilInstanceArgs,
    get_privileged_web3,
    get_unprivileged_web3,
    get_player_account,
    anvil_instance as anvil_config,
    format_anvil_args,
)
from ctf_launchers.utils import deploy, recv_until


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

# Challenge configuration
CHALLENGE = os.getenv("CHALLENGE", "challenge")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "http://127.0.0.1")
ETH_RPC_URL = os.getenv("ETH_RPC_URL", "None")
TIMEOUT = int(os.getenv("TIMEOUT", "111440"))
PROXY_PORT = os.getenv("PROXY_PORT", "28545")
FLAG = os.getenv("FLAG", "0ops{you_should_set_the_FLAG_env_var}")
PROJECT_LOCATION = "challenge/project"

ANVIL_IP = os.getenv("ANVIL_IP", "127.0.0.1")
ANVIL_PORT = os.getenv("ANVIL_PORT", "18545")
anvil_instance = {
    "ip": ANVIL_IP,
    "port": ANVIL_PORT,
}

# Global state for challenge instances
user_data = {}
session = None
instance_starting = False  # 标记实例是否正在启动

def load_user_data():
    """Load user data from file"""
    global user_data
    if not os.path.exists("userdata.json"):
        with open("userdata.json", "w") as f:
            f.write("{}")
    
    with open("userdata.json", "r") as f:
        user_data = json.loads(f.read())

def save_user_data():
    """Save user data to file"""
    with open("userdata.json", "w") as f:
        f.write(json.dumps(user_data))

def get_anvil_instance(mnemonic: str) -> LaunchAnvilInstanceArgs:
    """Get anvil instance configuration"""
    # Only fork if ETH_RPC_URL environment variable is explicitly set
    fork_url = None
    if "ETH_RPC_URL" in os.environ:
        fork_url = ETH_RPC_URL
    
    return LaunchAnvilInstanceArgs(
        balance=1000,
        accounts=3,
        fork_url=fork_url,
        mnemonic=mnemonic,
        chain_id=1
    )

def deploy_challenge(mnemonic: str) -> str:
    """Deploy challenge contract"""
    web3 = get_privileged_web3()
    return deploy(web3, PROJECT_LOCATION, mnemonic, env={})

def is_solved(addr: str) -> bool:
    """Check if challenge is solved"""
    try:
        web3 = get_privileged_web3()
        (result,) = abi.decode(
            ["bool"],
            web3.eth.call(
                {
                    "to": addr,
                    "data": web3.keccak(text="isSolved()")[:4],
                }
            ),
        )
        return result
    except Exception:
        return False

async def launch_new_instance():
    """Launch a new challenge instance"""
    global user_data, instance_starting
    
    instance_starting = True
    
    try:
        # Generate new mnemonic
        mnemonic = generate_mnemonic(12, lang="english")
        
        # Start anvil instance
        anvil_instances = get_anvil_instance(mnemonic)
        cmd_args = format_anvil_args(anvil_instances, port=anvil_config["port"])
        
        p = subprocess.Popen(
            ["anvil"] + cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        recv_until(p, b"Listening")
        
        # Deploy challenge
        challenge_addr = deploy_challenge(mnemonic)
        
        # Update user data
        user_data.update({
            "mnemonic": mnemonic,
            "challenge_address": challenge_addr
        })
        save_user_data()
        
        return {
            "mnemonic": mnemonic,
            "private_key": get_player_account(mnemonic).key.hex(),
            "challenge_address": challenge_addr,
            "rpc_url": f"{PUBLIC_HOST}:{PROXY_PORT}"
        }
    except Exception as e:
        raise e
    finally:
        instance_starting = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global session
    session = aiohttp.ClientSession()
    load_user_data()

    yield

    await session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that provides challenge information and checks for completion"""
    global user_data, instance_starting
    
    # Check if instance is currently starting
    if instance_starting:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Instance Starting...</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="5">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ color: #f39c12; border-bottom: 2px solid #f39c12; padding-bottom: 20px; margin-bottom: 30px; }}
                .info-box {{ background-color: #fdf2e9; padding: 15px; border-left: 4px solid #f39c12; margin: 15px 0; }}
                .spinner {{ display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #f39c12; animation: spin 2s linear infinite; margin-right: 15px; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                .loading {{ display: flex; align-items: center; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏳ Challenge Instance Starting...</h1>
                    <p>Please wait while we create your dedicated Ethereum environment</p>
                </div>
                
                <div class="info-box">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>Starting Anvil instance and deploying challenge contract...</span>
                    </div>
                </div>
                
                <div class="info-box">
                    <h3>🔄 Current Operations</h3>
                    <ul>
                        <li>✅ Generating mnemonic and private key</li>
                        <li>🔄 Starting local blockchain node</li>
                        <li>⏳ Deploying challenge smart contract</li>
                        <li>⏳ Configuring environment parameters</li>
                    </ul>
                </div>
                
                <div class="info-box">
                    <h3>💡 Note</h3>
                    <p>This process usually takes a few seconds.</p>
                    <p>The page will auto-refresh every 5 seconds, or you can manually refresh.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    
    # Check if instance exists
    if not user_data.get("challenge_address"):
        # Start instance creation in background
        if not instance_starting:
            # Start instance creation as background task
            asyncio.create_task(launch_new_instance())
        
        # Return loading page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Instance Starting...</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="3">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ color: #f39c12; border-bottom: 2px solid #f39c12; padding-bottom: 20px; margin-bottom: 30px; }}
                .info-box {{ background-color: #fdf2e9; padding: 15px; border-left: 4px solid #f39c12; margin: 15px 0; }}
                .spinner {{ display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #f39c12; animation: spin 2s linear infinite; margin-right: 15px; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                .loading {{ display: flex; align-items: center; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Creating Challenge Instance...</h1>
                    <p>First-time access requires setting up a dedicated Ethereum environment</p>
                </div>
                
                <div class="info-box">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>Starting Anvil instance and deploying challenge contract...</span>
                    </div>
                </div>
                
                <div class="info-box">
                    <h3>🔄 Current Operations</h3>
                    <ul>
                        <li>🔄 Generating mnemonic and private key</li>
                        <li>🔄 Starting local blockchain node</li>
                        <li>🔄 Deploying challenge smart contract</li>
                        <li>🔄 Configuring environment parameters</li>
                    </ul>
                </div>
                
                <div class="info-box">
                    <h3>💡 Note</h3>
                    <p>This process usually takes 10-30 seconds.</p>
                    <p>The page will auto-refresh every 3 seconds, and will show challenge info when complete.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    
    # Instance exists, check if solved
    challenge_address = user_data["challenge_address"]
    mnemonic = user_data["mnemonic"]
    private_key = get_player_account(mnemonic).key.hex()
    rpc_url = f"{PUBLIC_HOST}:{PROXY_PORT}"
    
    solved = is_solved(challenge_address)
    
    if solved:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Challenge Completed!</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ color: #27ae60; border-bottom: 2px solid #27ae60; padding-bottom: 20px; margin-bottom: 30px; }}
                .info-box {{ background-color: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
                .success {{ border-left-color: #27ae60; background-color: #d5f4e6; }}
                .flag {{ border-left-color: #f39c12; background-color: #fdf2e9; }}
                pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .flag-text {{ background: #27ae60; color: white; font-size: 18px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Congratulations! Challenge Completed!</h1>
                    <p>You have successfully solved the Ethereum challenge</p>
                </div>
                
                <div class="info-box flag">
                    <h3>🚩 Your Flag</h3>
                    <pre class="flag-text">{FLAG}</pre>
                </div>
                
                <div class="info-box">
                    <h3>🔗 RPC Endpoint</h3>
                    <pre>{rpc_url}</pre>
                </div>
                
                <div class="info-box">
                    <h3>🔑 Player Private Key</h3>
                    <pre>{private_key}</pre>
                </div>
                
                <div class="info-box">
                    <h3>🏆 Challenge Contract Address</h3>
                    <pre>{challenge_address}</pre>
                </div>
                
                <div class="info-box success">
                    <h3>✅ Challenge Status</h3>
                    <p><strong>Completed!</strong> You successfully called the solve() function.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    else:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ethereum Challenge</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }}
                .info-box {{ background-color: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
                .challenge {{ border-left-color: #e74c3c; background-color: #fadbd8; }}
                .pending {{ border-left-color: #f39c12; background-color: #fdf2e9; }}
                pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Ethereum Challenge in Progress</h1>
                    <p>Your instance is running, waiting for challenge completion</p>
                </div>
                
                <div class="info-box">
                    <h3>🔗 RPC Endpoint</h3>
                    <pre>{rpc_url}</pre>
                </div>
                
                <div class="info-box">
                    <h3>🔑 Player Private Key</h3>
                    <pre>{private_key}</pre>
                </div>
                
                <div class="info-box">
                    <h3>🏆 Challenge Contract Address</h3>
                    <pre>{challenge_address}</pre>
                </div>
                
                <div class="info-box pending">
                    <h3>⏳ Challenge Status</h3>
                    <p><strong>Pending Completion</strong> - Please call the contract's solve() function</p>
                </div>
                
                <div class="info-box challenge">
                    <h3>📋 Challenge Description</h3>
                    <p>Call the challenge contract's <code>solve()</code> function to complete the challenge!</p>
                    <p>Refresh this page after completion to see the flag.</p>
                </div>
                
                <div class="info-box">
                    <h3>💡 How to Use</h3>
                    <p>1. Use the RPC endpoint above to connect to your private blockchain</p>
                    <p>2. Use the provided private key as your account</p>
                    <p>3. Interact with the challenge contract to complete the challenge</p>
                    <p>4. Refresh this page to check completion status and get the flag</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content


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
    global session
    instance_host = f"http://{anvil_instance['ip']}:{anvil_instance['port']}"

    try:
        if session is None:
            return jsonrpc_fail(request_id, -32602, "Session not initialized")
        async with session.post(instance_host, json=body) as resp:
            return await resp.json()
    except Exception as e:
        logging.error(
            "failed to proxy anvil request to ", exc_info=e
        )
        return jsonrpc_fail(request_id, -32602, str(e))


@app.post("/")
@app.post("/rpc")
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

@app.websocket("/ws")
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
