# Aave USDC/aUSDC Exchange Calculator

A Python tool to calculate exchange rates between USDC and aUSDC using Aave V2 protocol's smart contracts.

## Overview

Calculate exchange amounts for:
- USDC → aUSDC (deposit)
- aUSDC → USDC (withdrawal)

## Prerequisites

- Python 3.7+
- Infura account

## Installation

1. Clone and setup:
```bash
# Clone repository
git clone https://github.com/sprnjt/aavetest.git
cd aavetest

# Install dependencies
pip install -r requirements.txt

# Create abis directory
mkdir abis

# Setup environment
cp .env.example .env
```

2. Add ABI files to `abis/` directory:
- `lending_pool_abi.json`
- `atoken_abi.json`

## Usage

```python
from aave_exchange_calculator import AaveDataProvider, AaveCalculator

# Initialize provider
provider = AaveDataProvider()

# Get current rates
normalized_income = provider.get_normalized_income()

# Calculate exchange amounts
usdc_amount = 1000 * 10**6  # 1000 USDC
ausdc_amount = AaveCalculator.calculate_ausdc_for_usdc(usdc_amount, normalized_income)
```

Run example:
```bash
python aave_exchange_calculator.py
```

## Contract Addresses

Ethereum Mainnet:
- Lending Pool: `0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9`
- USDC: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
- aUSDC: `0xBcca60bB61934080951369a648Fb03DF4F96263C`

## Project Structure

```
aavetest/
├── abis/
│   ├── lending_pool_abi.json
│   └── atoken_abi.json
├── .env.example
├── .gitignore
├── requirements.txt
├── aave_exchange_calculator.py
└── README.md
```

## Acknowledgments

- [Aave Protocol](https://aave.com/)
- [Web3.py](https://web3py.readthedocs.io/)
- [Infura](https://infura.io/)
