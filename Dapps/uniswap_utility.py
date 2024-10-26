import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web3utility import Web3Utility
import json

# Constants
UNISWAP_V3_ROUTER2_ADDRESS = '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45'

# Load ABI
with open('Dapps/UniswapV3Router2.json', mode='r') as file:
    UNI_V3_ROUTER2_ABI = json.load(file)

class Uniutility(Web3Utility):
    """
    Utility class for interacting with Uniswap V3 Router contract.
    Provides methods for decoding multicall data and path encoding/decoding.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        rpc_key: Optional[str] = None,
        chain: Optional[str] = None,
        contract_address: str = UNISWAP_V3_ROUTER2_ADDRESS,
        abi: List[Dict[str, Any]] = UNI_V3_ROUTER2_ABI,
        user_address: Optional[str] = None
    ) -> None:
        """
        Initialize the Uniswap utility.
        
        Args:
            rpc_url: RPC endpoint URL
            rpc_key: RPC API key
            chain: Blockchain network name
            contract_address: Uniswap V3 Router contract address
            abi: Contract ABI
            user_address: User's wallet address
        """
        super().__init__(
            rpc_url=rpc_url,
            rpc_key=rpc_key,
            chain=chain,
            contract_address=contract_address,
            abi=abi,
            user_address=user_address
        )

    def decode_multicall(self, input_data: str) -> Dict[str, Any]:
        """
        Decode Uniswap V3 multicall transaction input data.
        
        Args:
            input_data: Hex string of encoded transaction data
            
        Returns:
            Decoded transaction data and function calls
        """
        print("=== Multicall Decode Results ===")
        self.main_decoded = self.contract.decode_function_input(input_data)
        print(f"Main function: {self.main_decoded[0].fn_name}")

        for index, call_data in enumerate(self.main_decoded[1]['data']):
            inner_call = self.contract.decode_function_input(call_data)
            
            print(f"\nCall #{index + 1}:")
            print(f"Function: {inner_call[0].fn_name}")
            print("Parameters:")
            for key, value in inner_call[1].items():
                print(f"  {key}: {value}")
            print("-" * 50)

        return self.main_decoded

    def decode_multicall_path(self, path_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Decode Uniswap V3 path data.
        
        The path structure is: [token1, fee1, token2, fee2, token3, ...]
        - Each token address is 20 bytes
        - Each fee value is 3 bytes
        
        Args:
            path_bytes: Encoded path bytes
            
        Returns:
            List of decoded path elements (tokens and fees)
        """
        if len(path_bytes) < 23:  # Minimum length: token(20) + fee(3)
            raise ValueError("Path too short")

        path_length = len(path_bytes)
        print(f"Total path length: {path_length} bytes")
        
        current_position = 0
        token_number = 1
        decoded_path = []
        
        while current_position < path_length:
            # Get token address (20 bytes)
            if current_position + 20 > path_length:
                break
                
            token = '0x' + path_bytes[current_position:current_position + 20].hex()
            decoded_path.append({"type": "token", "value": token})
            print(f"Token {token_number}: {token}")
            current_position += 20
            
            # Get fee (3 bytes)
            if current_position + 3 <= path_length:
                fee = int.from_bytes(path_bytes[current_position:current_position + 3], 'big')
                decoded_path.append({"type": "fee", "value": fee})
                print(f"Fee: {fee} ({fee/10000}%)")
                current_position += 3
                token_number += 1

        return decoded_path