# Eth-Chall-Env

A simplified and modernized version of [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure) for easier deployment of Ethereum CTF challenges.

## Overview

This project provides a streamlined, single-service environment for deploying Ethereum CTF challenges. It features a unified HTTP service that combines challenge management, RPC proxy functionality, and a modern web interface. Compared to the original paradigm-ctf-infrastructure project, it simplifies deployment by consolidating all functionality into a single port while maintaining full compatibility with Ethereum tooling.

## Key Features

- **Unified HTTP Service**
  - Single port (28545) for both web interface and RPC
  - Modern web UI with real-time challenge status
  - Automatic instance creation and management
  - Built-in challenge completion detection

- **Private Blockchain Environment**
  - Anvil as local Ethereum node
  - Configurable chain ID and account numbers
  - Smart forking (only when ETH_RPC_URL is set)
  - Faster startup for local-only testing

- **Challenge Management**
  - Automated contract deployment process
  - Real-time status tracking
  - Flag delivery upon completion
  - Asynchronous instance creation

- **Account Management**
  - Automatic player account and private key generation
  - Preset account balances
  - Secure key management

- **Network Services**
  - HTTP and WebSocket RPC support
  - Built-in RPC request filtering and security checks
  - Responsive web interface
  - Auto-refresh during setup

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
docker compose build
```

3. Start services:
```bash
docker compose up
```

### Usage Guide

1. After services start, access the challenge:
   - Open your browser and navigate to `http://localhost:28545`
   - The web interface will automatically create a new challenge instance on first visit

2. Challenge instance creation:
   - The system automatically generates a mnemonic and private key
   - Starts a local Anvil blockchain node
   - Deploys the challenge contract
   - Displays all necessary information on the web page

3. Interact with the challenge:
   - Use the displayed RPC endpoint (`http://localhost:28545`) in your Ethereum tools
   - Import the provided private key into your wallet
   - Call the challenge contract's `solve()` function
   - Refresh the page to see your flag upon completion

4. RPC Usage:
   ```bash
   # Example RPC call
   curl -X POST http://localhost:28545 \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

## Project Structure

```
eth-chall-env/
├── ctf_launchers/           # Core utility modules
│   ├── types.py            # Type definitions and Web3 utilities
│   └── utils.py            # Deployment and utility functions
├── ctf_server/             # Unified HTTP service
│   └── anvil_proxy.py      # Main server with web UI and RPC proxy
├── challenge/              # Challenge contracts
│   └── project/           # Foundry project with Solidity contracts
├── docker-compose.yml      # Docker compose configuration
├── Dockerfile             # Docker build configuration
└── run.sh                 # Service startup script
```

## Configuration

The following parameters can be configured through environment variables:

- `PUBLIC_HOST`: Public address for RPC endpoint display (default: http://127.0.0.1)
- `PROXY_PORT`: HTTP service port (default: 28545)
- `ANVIL_PORT`: Internal Anvil node port (default: 18545)
- `ETH_RPC_URL`: Ethereum RPC URL for forking (optional - only fork if set)
- `TIMEOUT`: Instance timeout in seconds (default: 111440)
- `FLAG`: CTF flag value displayed upon challenge completion

### Environment Examples

For local testing (no forking):
```bash
export FLAG="flag{your_custom_flag_here}"
docker compose up
```

For mainnet forking:
```bash
export ETH_RPC_URL="https://mainnet.infura.io/v3/your-api-key"
export FLAG="flag{your_custom_flag_here}"
docker compose up
```

## Development Guide

### Adding New Challenges

1. **Create Smart Contracts**:
   ```solidity
   // challenge/project/src/YourChallenge.sol
   contract YourChallenge {
       bool private solved;
       
       function solve() external {
           // Your challenge logic here
           solved = true;
       }
       
       function isSolved() external view returns (bool) {
           return solved;
       }
   }
   ```

2. **Update Deployment Script**:
   - Modify `challenge/project/script/Deploy.s.sol` to deploy your contract
   - Ensure the deployment returns the challenge contract address

3. **Test Locally**:
   ```bash
   cd challenge/project
   forge test
   forge build
   ```

### Customizing the Environment

1. **Modify Anvil Configuration**:
   - Edit `get_anvil_instance()` in `ctf_server/anvil_proxy.py`
   - Adjust account numbers, balances, or chain ID

2. **Custom Challenge Logic**:
   - Override `is_solved()` function for complex completion criteria
   - Modify the web interface templates as needed

3. **Advanced RPC Filtering**:
   - Update `ALLOWED_NAMESPACES` and `DISALLOWED_METHODS` in `anvil_proxy.py`
   - Add custom validation logic in `validate_request()`

## Security Considerations

- **RPC Filtering**: Only allows safe Web3 methods (`web3`, `eth`, `net` namespaces)
- **Method Restrictions**: Blocks dangerous methods like `eth_sign`, `eth_sendTransaction`
- **Key Management**: Private keys are securely generated per instance
- **Container Isolation**: Complete isolation through Docker containerization
- **Timeout Protection**: Automatic cleanup prevents resource exhaustion
- **No Persistent Data**: Each instance starts fresh with no stored state

## Architecture Benefits

- **Single Port**: Simplified deployment with only one exposed port (28545)
- **No Database**: Stateless design eliminates database dependencies
- **Fast Startup**: Local-only mode starts in seconds without network dependencies
- **Modern Interface**: Responsive web UI with real-time status updates
- **Developer Friendly**: Standard Ethereum tooling compatibility

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check if port 28545 is in use
   lsof -i :28545
   
   # Modify port in docker-compose.yml if needed
   ports:
     - "8545:28545"  # Use port 8545 instead
   ```

2. **Instance Creation Fails**:
   - Check Docker logs: `docker compose logs`
   - Ensure Foundry is properly installed in container
   - Verify contract compilation: `cd challenge/project && forge build`

3. **RPC Connection Issues**:
   - Verify service is running: `curl http://localhost:28545/`
   - Check if the web interface loads
   - Ensure no firewall blocking the port

4. **Challenge Not Completing**:
   - Verify the `solve()` function was called successfully
   - Check transaction receipts for errors
   - Refresh the web page to update status

### Development Tips

- Use `docker compose logs -f` to monitor real-time logs
- For faster development, mount local files as volumes
- Test contracts locally with `forge test` before deployment


## Acknowledgements

This project is based on the excellent work done by the Paradigm team in their [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure). We are grateful for their contributions to the Ethereum security community and for open-sourcing their CTF infrastructure.

## License

This project is licensed under the MIT License.
