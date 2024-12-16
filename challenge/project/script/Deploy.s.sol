// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";
import "src/Challenge.sol";

contract Deploy is Script {
    function setUp() public {}

    function run() public {
        address system = getAddress(1);

        address challenge = deploy(system);

        vm.writeFile(vm.envOr("OUTPUT_FILE", string("/tmp/deploy.txt")), vm.toString(challenge));
    }

    function deploy(address system) internal returns (address challenge) {
        vm.startBroadcast(system);
        address player = getAddress(0);
        challenge = address(new Challenge(player));
        vm.stopBroadcast();
    }

    function getAdditionalAddress(uint32 index) internal returns (address) {
        return getAddress(index + 2);
    }

    function getPrivateKey(uint32 index) private returns (uint256) {
        string memory mnemonic =
            vm.envOr("MNEMONIC", string("test test test test test test test test test test test junk"));
        return vm.deriveKey(mnemonic, index);
    }

    function getAddress(uint32 index) private returns (address) {
        return vm.addr(getPrivateKey(index));
    }
}
