# Eth-Chall-Env

A simplified version of [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure) for easier deployment of Ethereum CTF challenges.

## Overview

This project provides a streamlined environment for deploying Ethereum CTF challenges. Compared to the original paradigm-ctf-infrastructure project, it removes complex features like databases and container distribution systems, retaining only the core blockchain environment and challenge deployment functionality. All components are consolidated into a single Docker container.

## Key Features

- **Private Blockchain Environment**
  - Anvil as local Ethereum node
  - Configurable chain ID and account numbers
  - Support for blockchain forking and state management

- **Challenge Deployment**
  - Automated contract deployment process

- **Account Management**
  - Automatic player account and private key generation
  - Preset account balances
  - Secure key management

- **Network Services**
  - Exposed RPC endpoint (default port: 28545)
  - WebSocket connection support
  - Built-in RPC request filtering and security checks

## Quick Start

### Prerequisites
- Docker
- Python 3.11+
- Foundry toolchain

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/eth-chall-env.git
cd eth-chall-env
```

2. Build Docker image:
```bash
docker-compose build
```

3. Start services:
```bash
docker-compose up
```

### Usage Guide

1. After services start, access through:
   - Challenge interface: `localhost:1337`
   - RPC endpoint: `localhost:28545`

2. Deploy new challenge instance:
   - Connect to challenge interface
   - Select "launch new instance" option
   - Wait for deployment and get instance info

3. Interact with challenge:
   - Connect to private blockchain using provided RPC endpoint
   - Sign transactions with provided private key
   - Interact with deployed contracts

## Project Structure

```
eth-chall-env/
├── ctf_launchers/     # Core launcher code
├── ctf_server/        # RPC proxy server
├── challenge/         # Challenge contracts
│   └── project/      # Foundry project
├── docker-compose.yml # Docker compose config
└── Dockerfile        # Docker build file
```

## Configuration

The following parameters can be configured through environment variables:

- `PUBLIC_HOST`: RPC service public address (default: http://127.0.0.1)
- `PROXY_PORT`: RPC proxy port (default: 28545)
- `ANVIL_PORT`: Anvil node port (default: 18545)
- `TIMEOUT`: Instance timeout (default: 111440)
- `FLAG`: CTF flag value

## Development Guide

1. Adding New Challenges:
   - Create new contracts under `challenge/project/`
   - Implement `isSolved()` interface
   - Write deployment scripts

2. Customizing Launcher:
   - Inherit from `PwnChallengeLauncher` class
   - Override `get_anvil_instance()` method for environment configuration
   - Customize deployment logic as needed

## Security Considerations

- RPC endpoint is filtered to prevent unauthorized methods
- Private keys are securely generated and managed
- Instance isolation through Docker containerization
- Timeout mechanism to prevent resource exhaustion

## Troubleshooting

Common issues and solutions:

1. Port conflicts:
   - Check if ports 1337 or 28545 are already in use
   - Modify port mappings in docker-compose.yml

2. Deployment failures:
   - Verify Foundry installation
   - Check contract compilation errors
   - Ensure sufficient gas for deployment

3. Connection issues:
   - Confirm Docker container is running
   - Verify network configurations
   - Check firewall settings

## Acknowledgements

This project is based on the excellent work done by the Paradigm team in their [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure). We are grateful for their contributions to the Ethereum security community and for open-sourcing their CTF infrastructure.

## License

This project follows the same licensing as the original paradigm-ctf-infrastructure.
