from web3 import Web3
from typing import Dict, Optional
from decimal import Decimal
import json
from pathlib import Path
import os
from dotenv import load_dotenv

env_path = Path('.env')
if not env_path.exists():
    raise FileNotFoundError(
        "No .env file found. Please create one using .env.example as a template"
    )
load_dotenv(env_path)

class AaveDataProvider:
    """Data provider for fetching on-chain data from Aave contracts"""
    
    def __init__(self, infura_api_key: str = None):
        self.api_key = infura_api_key or os.getenv('INFURA_API_KEY')
        if not self.api_key:
            raise ValueError("No Infura API key provided. Set INFURA_API_KEY environment variable or pass it to the constructor.")
            
        # Create RPC URL
        self.rpc_url = f"https://mainnet.infura.io/v3/{self.api_key}"
        
        # Mainnet contract addresses
        self.addresses = {
            'lending_pool': Web3.to_checksum_address('0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'),
            'usdc': Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'),
            'ausdc': Web3.to_checksum_address('0xBcca60bB61934080951369a648Fb03DF4F96263C')
        }
        
        self._normalized_income: Optional[int] = None
        self._ray: Optional[int] = None
        
        try:
            # Initialize Web3 connection with retry mechanism
            self.w3 = self._initialize_web3(self.rpc_url)
            
            # Load ABIs and initialize contracts
            self.contracts = self._initialize_contracts()
            
        except Exception as e:
            raise Exception(f"Failed to initialize AaveDataProvider: {str(e)}")

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
        """Initialize contract instances"""
        try:
            return {
                'lending_pool': self.w3.eth.contract(
                    address=self.addresses['lending_pool'],
                    abi=self._load_abi('lending_pool_abi.json')
                ),
                'ausdc': self.w3.eth.contract(
                    address=self.addresses['ausdc'],
                    abi=self._load_abi('atoken_abi.json')
                )
            }
        except Exception as e:
            raise Exception(f"Failed to initialize contracts: {str(e)}")

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

    def get_normalized_income(self) -> int:
        """Get current normalized income for aUSDC with caching"""
        if self._normalized_income is None:
            try:
                self._normalized_income = self.contracts['ausdc'].functions.getNormalizedIncome().call()
            except Exception as e:
                raise Exception(f"Failed to get normalized income: {str(e)}")
        return self._normalized_income

    def get_ray(self) -> int:
        """Get RAY constant used in calculations with caching"""
        if self._ray is None:
            try:
                self._ray = self.contracts['ausdc'].functions.RAY().call()
            except Exception as e:
                raise Exception(f"Failed to get RAY value: {str(e)}")
        return self._ray

    def refresh_data(self) -> None:
        """Force refresh of cached data"""
        self._normalized_income = None
        self._ray = None


class AaveCalculator:
    """Calculator for USDC/aUSDC exchange rates"""
    
    RAY = Decimal('1e27') 
    USDC_DECIMALS = Decimal('1e6')
    
    @classmethod
    def calculate_ausdc_for_usdc(cls, usdc_amount: int, normalized_income: int) -> int:
        """
        Calculate how much aUSDC will be received for a given USDC amount
        Args:
            usdc_amount: Amount of USDC (in base units with 6 decimals)
            normalized_income: Current normalized income from aToken contract
        Returns:
            Amount of aUSDC to be received
        """
        cls._validate_inputs(usdc_amount, normalized_income)
        
        try:
            normalized_income_decimal = Decimal(str(normalized_income))
            usdc_decimal = Decimal(str(usdc_amount))
            
            result = (usdc_decimal * cls.RAY * cls.RAY) / (cls.USDC_DECIMALS * normalized_income_decimal)
            
            return int(result)
        except Exception as e:
            raise Exception(f"Failed to calculate aUSDC amount: {str(e)}")

    @classmethod
    def calculate_usdc_for_ausdc(cls, ausdc_amount: int, normalized_income: int) -> int:
        """
        Calculate how much USDC will be received for a given aUSDC amount
        Args:
            ausdc_amount: Amount of aUSDC (in base units)
            normalized_income: Current normalized income from aToken contract
        Returns:
            Amount of USDC to be received
        """
        cls._validate_inputs(ausdc_amount, normalized_income)
        
        try:
   
            normalized_income_decimal = Decimal(str(normalized_income))
            ausdc_decimal = Decimal(str(ausdc_amount))
            
            
            result = (ausdc_decimal * normalized_income_decimal * cls.USDC_DECIMALS) / (cls.RAY * cls.RAY)
            
            return int(result)
        except Exception as e:
            raise Exception(f"Failed to calculate USDC amount: {str(e)}")

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
        # Create provider instance using environment variable
        data_provider = AaveDataProvider()
        
        # Get current exchange rates from blockchain
        normalized_income = data_provider.get_normalized_income()
        
        # Test amounts
        test_amounts = [int(amount * 10**6) for amount in [1, 100, 1000]]
        
        print("\nUSDC to aUSDC Exchange Rates:")
        print("-" * 50)
        
        for usdc_amount in test_amounts:
            try:
                # Calculate exchange amounts
                ausdc_amount = AaveCalculator.calculate_ausdc_for_usdc(
                    usdc_amount,
                    normalized_income
                )
                
                usdc_received = AaveCalculator.calculate_usdc_for_ausdc(
                    ausdc_amount,
                    normalized_income
                )
                
                # Print results
                print(f"\nDeposit {format_amount(usdc_amount, 6)} USDC:")
                print(f"Receive: {format_amount(ausdc_amount, 6)} aUSDC")
                print(f"Withdrawable USDC: {format_amount(usdc_received, 6)} USDC")
                
            except Exception as e:
                print(f"Error calculating for amount {format_amount(usdc_amount, 6)} USDC: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}") 