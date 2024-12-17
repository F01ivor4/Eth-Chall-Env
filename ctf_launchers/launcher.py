import abc
import os
import subprocess
import traceback
from dataclasses import dataclass
from typing import Callable, Dict, List

from ctf_launchers.types import (
    LaunchAnvilInstanceArgs,
    get_privileged_web3,
    get_unprivileged_web3,
    get_player_account,
    anvil_instance,
    format_anvil_args,

)
import requests
from eth_account.hdaccount import generate_mnemonic
from ctf_launchers.utils import deploy, recv_until
import json


CHALLENGE = os.getenv("CHALLENGE", "challenge")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "http://127.0.0.1")

ETH_RPC_URL = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
TIMEOUT = int(os.getenv("TIMEOUT", "111440"))

PROXY_PORT = os.getenv("PROXY_PORT", "28545")


@dataclass
class Action:
    name: str
    handler: Callable[[], int]


class Launcher(abc.ABC):
    def __init__(self, project_location: str, actions: List[Action] = []):
        self.project_location = project_location

        self._actions = [
            Action(name="launch new instance", handler=self.launch_instance),
        ] + actions
        
        if not os.path.exists("userdata.json"):
            with open("userdata.json", "w") as f:
                f.write("{}")
        
        with open("userdata.json", "r") as f:
            self.user_data = json.loads(f.read())

    def run(self):
        self.mnemonic = generate_mnemonic(12, lang="english")
        for i, action in enumerate(self._actions):
            print(f"{i+1} - {action.name}")

        try:
            handler = self._actions[int(input("action? ")) - 1]
        except:
            print("Oops, can you not")
            exit(1)

        try:
            exit(handler.handler())
        except Exception as e:
            traceback.print_exc()
            print("an error occurred", e)
            exit(1)

    def _get_anvil_instance(self, **kwargs) -> LaunchAnvilInstanceArgs:
        if not "balance" in kwargs:
            kwargs["balance"] = 1000
        if not "accounts" in kwargs:
            kwargs["accounts"] = 2
        if not "fork_url" in kwargs:
            kwargs["fork_url"] = ETH_RPC_URL
        if not "mnemonic" in kwargs:
            kwargs["mnemonic"] = self.mnemonic
        return LaunchAnvilInstanceArgs(
            **kwargs,
        )

    def get_anvil_instance(self, **kwargs) -> LaunchAnvilInstanceArgs:
        return self._get_anvil_instance(**kwargs)

    def update_metadata(self, new_metadata: Dict[str, str]):
        self.user_data.update(new_metadata)
        with open("userdata.json", "w") as f:
            f.write(json.dumps(self.user_data))

    def launch_instance(self) -> int:
        user_data = self.get_user_data()
        if user_data.get("challenge_address", None):
            print("you already have an instance running")
            return 1
        print("creating private blockchain...")
        anvil_instances = self.get_anvil_instance()
        cmd_args = format_anvil_args(anvil_instances, port=anvil_instance["port"])
        p = subprocess.Popen(
            ["anvil"] +
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        recv_until(p, b"Listening")

        print()
        print(f"your private blockchain has been set up")
        print(f"it will automatically terminate in {TIMEOUT} seconds")
        print(f"---")
        print(f"rpc endpoints:")
        print(f"    - {PUBLIC_HOST}:{PROXY_PORT}")
        print(f"private key:        {get_player_account(self.mnemonic).key.hex()}")

        print("waiting for instance to start...")
        print("deploying challenge...")
        challenge_addr = self.deploy(self.mnemonic)

        self.update_metadata(
            {"mnemonic": self.mnemonic, "challenge_address": challenge_addr}
        )

        self.user_data["challenge_address"] = challenge_addr
        print(f"challenge contract: {challenge_addr}")
        return 0

    def deploy(self, mnemonic: str) -> str:
        web3 = get_privileged_web3()

        return deploy(web3, self.project_location, mnemonic, env={})

    def get_user_data(self) -> Dict:
        return self.user_data
