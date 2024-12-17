# Eth-Chall-Env

A simplified version of [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure) for easier deployment of Ethereum CTF challenges.

## Overview

This project aims to provide a simplified environment for deploying Ethereum CTF challenges. Compared to the original paradigm-ctf-infrastructure project, it removes complex features like databases and container distribution systems, retaining only the core blockchain environment and challenge deployment functionality. All components are consolidated into a single Docker container.

## Key Changes from Original Project

- Consolidated multi-container setup into a single Docker container
- Simplified networking and infrastructure requirements
- Streamlined deployment process
- Maintained core functionality for challenge deployment and interaction

## Features

- Private Ethereum blockchain environment using Anvil
- Challenge deployment and instance management
- Player account management with private keys
- RPC endpoint exposure
- Simplified launcher interface

## Usage

1. Build the Docker container
2. Deploy challenges using the launcher interface
3. Access the private blockchain via exposed RPC endpoint
4. Interact with deployed challenge contracts

## Requirements

- Docker

## Acknowledgements

This project is based on the excellent work done by the Paradigm team in their [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure). We are grateful for their contributions to the Ethereum security community and for open-sourcing their CTF infrastructure.

## License

This project follows the same licensing as the original paradigm-ctf-infrastructure.
