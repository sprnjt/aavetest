from typing import Dict, NamedTuple

class TokenConfig(NamedTuple):
    underlying_address: str
    atoken_address: str
    decimals: int
    symbol: str
    description: str

# Aave V2 Mainnet Token Configurations
TOKENS: Dict[str, TokenConfig] = {
    # Stablecoins
    'USDC': TokenConfig(
        underlying_address='0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        atoken_address='0xBcca60bB61934080951369a648Fb03DF4F96263C',
        decimals=6,
        symbol='USDC',
        description='USD Coin'
    ),
    'USDT': TokenConfig(
        underlying_address='0xdAC17F958D2ee523a2206206994597C13D831ec7',
        atoken_address='0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811',
        decimals=6,
        symbol='USDT',
        description='Tether USD'
    ),
    'DAI': TokenConfig(
        underlying_address='0x6B175474E89094C44Da98b954EedeAC495271d0F',
        atoken_address='0x028171bCA77440897B824Ca71D1c56caC55b68A3',
        decimals=18,
        symbol='DAI',
        description='Dai Stablecoin'
    ),
    # Wrapped Assets
    'WETH': TokenConfig(
        underlying_address='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        atoken_address='0x030bA81f1c18d280636F32af80b9AAd02Cf0854e',
        decimals=18,
        symbol='WETH',
        description='Wrapped Ether'
    ),
    'WBTC': TokenConfig(
        underlying_address='0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        atoken_address='0x9ff58f4fFB29fA2266Ab25e75e2A8b3503311656',
        decimals=8,
        symbol='WBTC',
        description='Wrapped Bitcoin'
    )
} 