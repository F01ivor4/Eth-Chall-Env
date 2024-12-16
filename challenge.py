from typing import Dict

from eth_abi import abi

from ctf_launchers.pwn_launcher import PwnChallengeLauncher
from ctf_launchers.types import LaunchAnvilInstanceArgs, get_privileged_web3
from ctf_launchers.utils import deploy


class Challenge(PwnChallengeLauncher):
    def get_anvil_instance(self) -> LaunchAnvilInstanceArgs:
        return self._get_anvil_instance(chain_id=1, accounts=3)
    
    def deploy(self, mnemonic: str) -> str:
        geek_web3 = get_privileged_web3()

        challenge = deploy(
            geek_web3,
            self.project_location,
            mnemonic=mnemonic,
        )

        return challenge


Challenge().run()
