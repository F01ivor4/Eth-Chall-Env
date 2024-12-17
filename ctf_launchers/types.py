import os
import subprocess
from dataclasses import dataclass
from typing import Dict, List, NotRequired, Optional

from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.hdaccount import key_from_seed, seed_from_mnemonic
from typing_extensions import TypedDict
from web3 import Web3

DEFAULT_IMAGE = "ghcr.io/foundry-rs/foundry:latest"
DEFAULT_DERIVATION_PATH = "m/44'/60'/0'/0/"
DEFAULT_ACCOUNTS = 10
DEFAULT_BALANCE = 1000
DEFAULT_MNEMONIC = "test test test test test test test test test test test junk"

PUBLIC_HOST = os.getenv("PUBLIC_HOST", "http://127.0.0.1:28545")

ANVIL_IP = os.getenv("ANVIL_IP", "127.0.0.1")
ANVIL_PORT = os.getenv("ANVIL_PORT", "18545")

PROXY_PORT = os.getenv("PROXY_PORT", "28545")

anvil_instance = {
    "ip": ANVIL_IP,
    "port": ANVIL_PORT,
}


class LaunchAnvilInstanceArgs(TypedDict):
    image: NotRequired[Optional[str]]
    accounts: NotRequired[Optional[int]]
    balance: NotRequired[Optional[float]]
    derivation_path: NotRequired[Optional[str]]
    mnemonic: NotRequired[Optional[str]]
    fork_url: NotRequired[Optional[str]]
    fork_block_num: NotRequired[Optional[int]]
    fork_chain_id: NotRequired[Optional[int]]
    no_rate_limit: NotRequired[Optional[bool]]
    chain_id: NotRequired[Optional[int]]
    code_size_limit: NotRequired[Optional[int]]
    block_time: NotRequired[Optional[int]]


def format_anvil_args(args: LaunchAnvilInstanceArgs, port: int | str = 18545) -> List[str]:
    cmd_args = []
    cmd_args += ["--host", "0.0.0.0"]
    cmd_args += ["--port", str(port)]
    cmd_args += ["--accounts", str(args["accounts"])]
    cmd_args += ["--state", f"/data/state.json"]
    cmd_args += ["--state-interval", "5"]

    if args.get("fork_url") is not None:
        cmd_args += ["--fork-url", args["fork_url"]]

    if args.get("fork_chain_id") is not None:
        cmd_args += ["--fork-chain-id", str(args["fork_chain_id"])]

    if args.get("fork_block_num") is not None:
        cmd_args += ["--fork-block-number", str(args["fork_block_num"])]

    if args.get("no_rate_limit") == True:
        cmd_args += ["--no-rate-limit"]

    if args.get("chain_id") is not None:
        cmd_args += ["--chain-id", str(args["chain_id"])]

    if args.get("code_size_limit") is not None:
        cmd_args += ["--code-size-limit", str(args["code_size_limit"])]

    if args.get("block_time") is not None:
        cmd_args += ["--block-time", str(args["block_time"])]

    if args.get("mnemonic") is not None:
        cmd_args += ["--mnemonic", args["mnemonic"]]

    if args.get("derivation_path") is not None:
        cmd_args += ["--derivation-path", args["derivation_path"]]

    return cmd_args






class InstanceInfo(TypedDict):
    id: str
    ip: str
    port: int


@dataclass
class AnvilInstance:
    proc: subprocess.Popen
    id: str

    ip: str
    port: int





def get_account(mnemonic: str, offset: int) -> LocalAccount:
    seed = seed_from_mnemonic(mnemonic, "")
    private_key = key_from_seed(seed, f"{DEFAULT_DERIVATION_PATH}{offset}")

    return Account.from_key(private_key)


def get_player_account(mnemonic: str) -> LocalAccount:
    return get_account(mnemonic, 0)


def get_system_account(mnemonic: str) -> LocalAccount:
    return get_account(mnemonic, 1)


def get_additional_account(mnemonic: str, offset: int) -> LocalAccount:
    return get_account(mnemonic, offset + 2)


def get_privileged_web3() -> Web3:
    
    return Web3(
        Web3.HTTPProvider(f"http://{anvil_instance['ip']}:{anvil_instance['port']}")
    )


def get_unprivileged_web3() -> Web3:
    return Web3(
        Web3.HTTPProvider(
            f"http://127.0.0.1:{PROXY_PORT}",
        )
    )
