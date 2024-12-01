# Aave Token Exchange Calculator

Calculate exchange rates between tokens and their aTokens using Aave V2 protocol.

## Supported Tokens

Stablecoins:
- USDC (USD Coin, 6 decimals)
- USDT (Tether USD, 6 decimals)
- DAI (Dai Stablecoin, 18 decimals)

Wrapped Assets:
- WETH (Wrapped Ether, 18 decimals)
- WBTC (Wrapped Bitcoin, 8 decimals)

## Prerequisites

- Python 3.7+
- Infura account

## Quick Start

1. Setup:
```bash
git clone https://github.com/sprnjt/aavetest.git
cd aavetest
pip install -r requirements.txt
cp .env.example .env  # Add your Infura API key
```

2. Usage:
```python
from aave_exchange_calculator import AaveDataProvider, AaveCalculator
from token_config import TOKENS

provider = AaveDataProvider()
token_config = TOKENS['USDC']
normalized_income = provider.get_normalized_income('USDC')

# Calculate aToken amount for 1000 USDC
amount = 1000 * 10**token_config.decimals
atoken_amount = AaveCalculator.calculate_atoken_for_token(
    amount, 
    normalized_income,
    token_config
)
```

## Project Structure
```
aavetest/
├── abis/                    # Contract ABIs
├── aave_exchange_calculator.py
├── token_config.py          # Token configurations
├── requirements.txt         # Dependencies
└── README.md
```

## Acknowledgments
- [Aave Protocol](https://aave.com/)
- [Web3.py](https://web3py.readthedocs.io/)
- [Infura](https://infura.io/)
