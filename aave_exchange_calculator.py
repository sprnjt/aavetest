from web3 import Web3
from typing import Dict, Optional
from decimal import Decimal
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from token_config import TOKENS, TokenConfig

env_path = Path('.env')
if not env_path.exists():
    raise FileNotFoundError(
        "No .env file found. Please create one using .env.example as a template"
    )
load_dotenv(env_path)

class AaveDataProvider:
    """Data provider for fetching on-chain data from Aave contracts"""
    
    def __init__(self, infura_api_key: str = None):
        # Load environment and initialize Web3
        self.api_key = infura_api_key or os.getenv('INFURA_API_KEY')
        if not self.api_key:
            raise ValueError("No Infura API key provided")
            
        self.rpc_url = f"https://mainnet.infura.io/v3/{self.api_key}"
        
        # Initialize addresses with lending pool
        self.addresses = {
            'lending_pool': Web3.to_checksum_address('0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9')
        }
        # Add token addresses
        for symbol, config in TOKENS.items():
            self.addresses[symbol] = Web3.to_checksum_address(config.underlying_address)
            self.addresses[f'a{symbol}'] = Web3.to_checksum_address(config.atoken_address)
        
        # Cache for normalized income values
        self._normalized_incomes: Dict[str, Optional[int]] = {symbol: None for symbol in TOKENS}
        
        try:
            self.w3 = self._initialize_web3(self.rpc_url)
            self.contracts = self._initialize_contracts()
        except Exception as e:
            raise Exception(f"Failed to initialize: {str(e)}")

    def _initialize_web3(self, rpc_url: str, max_retries: int = 3) -> Web3:
        """Initialize Web3 with retry mechanism"""
        for attempt in range(max_retries):
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    # Verify contracts are deployed
                    for name, address in self.addresses.items():
                        if not w3.eth.get_code(address):
                            raise ValueError(f"No contract found at {name} address: {address}")
                    return w3
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Ethereum node after {max_retries} attempts: {str(e)}")
        raise ConnectionError("Failed to connect to Ethereum node")

    def _initialize_contracts(self) -> Dict:
        """Initialize contract instances for all tokens"""
        contracts = {
            'lending_pool': self.w3.eth.contract(
                address=self.addresses['lending_pool'],
                abi=self._load_abi('lending_pool_abi.json')
            )
        }
        
        # Initialize aToken contracts
        atoken_abi = self._load_abi('atoken_abi.json')
        for symbol, config in TOKENS.items():
            contracts[f'a{symbol}'] = self.w3.eth.contract(
                address=self.addresses[f'a{symbol}'],
                abi=atoken_abi
            )
            
        return contracts

    @staticmethod
    def _load_abi(filename: str) -> Dict:
        """Load ABI from json file with path handling"""
        try:
            abi_path = Path('abis') / filename
            if not abi_path.exists():
                raise FileNotFoundError(f"ABI file not found: {abi_path}")
            
            with abi_path.open() as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in ABI file: {filename}")

    def get_normalized_income(self, symbol: str) -> int:
        """Get normalized income for specific token"""
        if symbol not in TOKENS:
            raise ValueError(f"Unsupported token: {symbol}")
            
        if self._normalized_incomes[symbol] is None:
            contract = self.contracts[f'a{symbol}']
            self._normalized_incomes[symbol] = contract.functions.getNormalizedIncome().call()
            
        return self._normalized_incomes[symbol]

    def refresh_data(self, symbol: str = None):
        """Refresh cached data for one or all tokens"""
        if symbol:
            if symbol in self._normalized_incomes:
                self._normalized_incomes[symbol] = None
        else:
            self._normalized_incomes = {symbol: None for symbol in TOKENS}


class AaveCalculator:
    """Calculator for token/aToken exchange rates"""
    
    RAY = Decimal('1e27')
    
    @classmethod
    def calculate_atoken_for_token(cls, 
                                 amount: int, 
                                 normalized_income: int,
                                 token_config: TokenConfig) -> int:
        """Calculate aToken amount for given token amount"""
        cls._validate_inputs(amount, normalized_income)
        
        try:
            token_decimals = Decimal(f'1e{token_config.decimals}')
            amount_decimal = Decimal(str(amount))
            normalized_income_decimal = Decimal(str(normalized_income))
            
            result = (amount_decimal * cls.RAY * cls.RAY) / (token_decimals * normalized_income_decimal)
            
            return int(result)
        except Exception as e:
            raise Exception(f"Failed to calculate aToken amount: {str(e)}")

    @classmethod
    def calculate_token_for_atoken(cls,
                                 atoken_amount: int,
                                 normalized_income: int,
                                 token_config: TokenConfig) -> int:
        """Calculate token amount for given aToken amount"""
        cls._validate_inputs(atoken_amount, normalized_income)
        
        try:
            token_decimals = Decimal(f'1e{token_config.decimals}')
            atoken_decimal = Decimal(str(atoken_amount))
            normalized_income_decimal = Decimal(str(normalized_income))
            
            result = (atoken_decimal * normalized_income_decimal * token_decimals) / (cls.RAY * cls.RAY)
            
            return int(result)
        except Exception as e:
            raise Exception(f"Failed to calculate token amount: {str(e)}")

    @staticmethod
    def _validate_inputs(amount: int, normalized_income: int) -> None:
        """Validate input parameters"""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")
        if not isinstance(normalized_income, (int, float)) or normalized_income <= 0:
            raise ValueError("Normalized income must be a positive number")


def format_amount(amount: int, decimals: int) -> str:
    """Format token amount with proper decimals"""
    try:
        return f"{Decimal(str(amount)) / Decimal(10**decimals):.6f}"
    except Exception as e:
        raise ValueError(f"Failed to format amount: {str(e)}")


if __name__ == "__main__":
    try:
        data_provider = AaveDataProvider()
        
        # Test with different tokens
        test_amounts = {
            'USDC': 1000 * 10**6,    # 1000 USDC
            'DAI': 1000 * 10**18,    # 1000 DAI
            'WETH': 1 * 10**18,      # 1 WETH
            'WBTC': 1 * 10**8,       # 1 WBTC
            'USDT': 1000 * 10**6,    # 1000 USDT
        }
        
        print("\nAave V2 Token Exchange Rates:")
        print("-" * 50)
        
        for symbol, amount in test_amounts.items():
            try:
                token_config = TOKENS[symbol]
                normalized_income = data_provider.get_normalized_income(symbol)
                
                # Calculate exchange amounts
                atoken_amount = AaveCalculator.calculate_atoken_for_token(
                    amount,
                    normalized_income,
                    token_config
                )
                
                token_received = AaveCalculator.calculate_token_for_atoken(
                    atoken_amount,
                    normalized_income,
                    token_config
                )
                
                # Print results
                print(f"\n{token_config.description} ({symbol}) Exchange:")
                print(f"Deposit: {format_amount(amount, token_config.decimals)} {symbol}")
                print(f"Receive: {format_amount(atoken_amount, token_config.decimals)} a{symbol}")
                print(f"Withdrawable: {format_amount(token_received, token_config.decimals)} {symbol}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}") 