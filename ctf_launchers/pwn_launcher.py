import os

import requests
from eth_abi import abi

from ctf_launchers.launcher import Action, Launcher
from ctf_launchers.types import get_privileged_web3

FLAG = os.getenv("FLAG", "0ops{you_should_set_the_FLAG_env_var}")


class PwnChallengeLauncher(Launcher):
    def __init__(
        self,
        project_location: str = "challenge/project",
    ):
        super().__init__(
            project_location,
            [
                Action(name="get flag", handler=self.get_flag),
            ],
        )

    def get_flag(self) -> int:
        user_data = self.get_user_data()

        if not self.is_solved(user_data["challenge_address"]):
            print("Are you sure you solved it? :(")
            return 1

        print("🎉 Congratulations! Here is your flag 🚩")
        print(FLAG)
        return 0

    def is_solved(self, addr: str) -> bool:
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
