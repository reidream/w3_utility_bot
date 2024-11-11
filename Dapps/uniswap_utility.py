import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web3utility import Web3Utility

# Constants
UNISWAP_V3_ROUTER2_ADDRESS = '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45'
UNISWAP_V3_BASE_FACTORY = '0x33128a8fC17869897dcE68Ed026d694621f6FDfD'

# Load ABI
with open('Dapps/UniswapAbi/UniswapV3Router2.json', mode='r') as file:
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
        """Initialize the Uniswap utility.
        
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
        self.base_factory = self.w3.to_checksum_address(UNISWAP_V3_BASE_FACTORY)

    def decode_multicall(self, input_data: str) -> Dict[str, Any]:
        """Decode Uniswap V3 multicall transaction input data.
        
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

    def get_pool_address(self, 
                        tokenA: str = None,
                        tokenB: str = None,
                        poolFees: Dict[int, Any] = None) -> List[str]:
        """Get pool addresses for token pairs with specified fees."""
        with open("Dapps/UniswapAbi/UniswapV3_factroy_abi.json", mode="r") as file:
            uniswapV3_factroy_abi = json.load(file)
            
        uniV3_factory = self.w3.eth.contract(
            address=self.base_factory,
            abi=uniswapV3_factroy_abi
        )
        
        pools = []
        for poolFee in poolFees:
            pool = uniV3_factory.functions.getPool(
                tokenA,
                tokenB,
                poolFee
            ).call()
            pools.append(pool)
        return pools
    
    def exact_input(
        self,
        path: List[str],
        fee: int = 500,
        pool_address: str = None,
        path_forward: bool = True,
        recipient: str = None,
        amount_in: int = 0,
        slippage: float = 0.05,
        value: int = None,
        gaslimit: bool = False
    ) -> Dict[str, Any]:
        """Execute exact input swap."""
        # Create path data
        byte_token_a = self.w3.to_bytes(hexstr=path[0])
        byte_fee = fee.to_bytes(3, "big")
        byte_token_b = self.w3.to_bytes(hexstr=path[1])
        encoded_path = byte_token_a + byte_fee + byte_token_b

        # Calculate minimum output amount
        amount_out_minimum = self.simple_slippage(
            path=path_forward,
            pool_address=pool_address,
            amount_in=amount_in,
            slippage_percent=slippage
        )["min_amount_out"]

        params = {
            'path': encoded_path,
            'recipient': recipient,
            'amountIn': amount_in,
            'amountOutMinimum': amount_out_minimum
        }
        
        encoded_data = self.contract.encodeABI(fn_name="exactInput", args=[params])
        
        if gaslimit:
            gas_limit = self.estimate_gas_limit(
                params,
                function_name="exactInput",
                value=value
            )
            return {
                "encoded_exactInput": encoded_data,
                "gaslimit": gas_limit
            }
        return {"encoded_exactInput": encoded_data}

    def exactInputSingle(
        self,
        tokenIn: str = None,
        tokenOut: str = None,
        fee: int = None,
        poolAddres: str = None,
        path_forward: bool = True,
        recipient: str = None,
        amountIn: int = None,
        sllipage: float = None,
        sqrtPriceLimitX96: float = None,
        value: int = None,
        gaslimit: bool = False
    ) -> Dict[str, Any]:
        """Execute exact input single swap."""
        pool_info = self.simple_slippage(
            pool_address=poolAddres,
            path=path_forward,
            amount_in=amountIn,
            slippage_percent=sllipage
        )
        
        params = {
            'tokenIn': tokenIn,
            'tokenOut': tokenOut,
            'fee': fee,
            'recipient': recipient,
            'amountIn': amountIn,
            'amountOutMinimum': pool_info["min_amount_out"],
            'sqrtPriceLimitX96': int(pool_info["sqrt_price_x96"] * (100 + sqrtPriceLimitX96) / 100)
        }
        
        encoded_data = self.contract.encodeABI(fn_name="exactInputSingle", args=[params])
        
        if gaslimit:
            gas_limit = self.estimate_gas_limit(
                params,
                function_name="exactInputSingle",
                value=value
            )
            return {
                "encoded_exactInputsingle": encoded_data,
                "gaslimit": gas_limit
            }
        return {"encoded_exactInputSingle": encoded_data}
    
    def exact_output(
        self,
        path: List[str],
        fee: int = 500,
        pool_address: str = None,
        path_forward: bool = True,
        recipient: str = None,
        amount_out: int = 0,
        amountInMaximum: float = 1.05,
        value: int = None,
        gaslimit: bool = False
    ) -> Dict[str, Any]:
        """Execute exact output swap."""
        # Create path data
        byte_token_a = self.w3.to_bytes(hexstr=path[0])
        byte_fee = fee.to_bytes(3, "big")
        byte_token_b = self.w3.to_bytes(hexstr=path[1])
        encoded_path = byte_token_a + byte_fee + byte_token_b
        
        amount_out_minimum = self.simple_slippage(
            path=path_forward,
            pool_address=pool_address,
            amount_in=amount_out,
            slippage_percent=amountInMaximum
        )["min_amount_out"]

        params = {
            "path": encoded_path,
            "recipient": recipient,
            "amountOut": amount_out,
            "amountInMaximum": amount_out_minimum
        }

        encoded_data = self.contract.encodeABI(fn_name="exactOutput", args=[params])
        
        if gaslimit:
            gas_limit = self.estimate_gas_limit(
                params,
                function_name="exactOutput",
                value=value
            )
            return {
                "encoded_exactOutput": encoded_data,
                "gaslimit": gas_limit
            }
        return {"encoded_exactOutput": encoded_data}

    def exactOutputSingle(
        self,
        tokenIn: str = None,
        tokenOut: str = None,
        fee: int = None,
        poolAddres: str = None,
        path_forward: bool = True,
        recipient: str = None,
        amountOut: int = None,
        amountInMaximum: float = None,
        sqrtPriceLimitX96: float = None,
        value: int = None,
        gaslimit: bool = False
    ) -> Dict[str, Any]:
        """Execute exact output single swap."""
        pool_info = self.simple_slippage(
            pool_address=poolAddres,
            path=path_forward,
            amount_in=amountOut,
            slippage_percent=amountInMaximum
        )
        
        params = {
            'tokenIn': tokenIn,
            'tokenOut': tokenOut,
            'fee': fee,
            'recipient': recipient,
            'amountOut': amountOut,
            'amountInMaximum': pool_info["min_amount_out"],
            'sqrtPriceLimitX96': int(pool_info["sqrt_price_x96"] * (100 + sqrtPriceLimitX96) / 100)
        }
        
        encoded_data = self.contract.encodeABI(fn_name="exactOutputSingle", args=[params])
        
        if gaslimit:
            gas_limit = self.estimate_gas_limit(
                params,
                function_name="exactOutputSingle",
                value=value
            )
            return {
                "encoded_exactOutputsingle": encoded_data,
                "gaslimit": gas_limit
            }
        return {"encoded_exactOutputSingle": encoded_data}

    def multicall(
        self, 
        data_list: List[bytes],
        value: int = None,
        gaslimit: bool = True
    ) -> Dict[str, Any]:
        """Execute multiple calls in a single transaction."""
        encoded_data = self.contract.encodeABI(fn_name="multicall", args=[data_list])
       
        if gaslimit:
            gas_limit = self.estimate_gas_limit(
                [encoded_data],
                function_name="multicall",
                value=value
            )
            return {
                "encoded_multicall": encoded_data,
                "gaslimit": gas_limit
            }
        return {"encoded_multicall": encoded_data}


if __name__ == "__main__":
    # Example usage
    uni_bot = Uniutility(
        rpc_url=os.getenv("INFURA_URL"),
        rpc_key=os.getenv("RPC_KEY"),
        chain="base",
        contract_address="0x2626664c2603336E57B271c5C0b26F421741e481",
        user_address=os.getenv("ADDRESS")
    )

    # Token addresses
    USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    WETH = "0x4200000000000000000000000000000000000006"
    
    # Test amount (11 ETH)
    amount = int(11 * (10 ** 18))
    
    # Get pool address
    pool_address = uni_bot.get_pool_address(WETH, USDC, [500])

    # Get pool info and slippage calculations for 10 ETH
    pool_info = uni_bot.simple_slippage(
        pool_address=pool_address[0],
        path=True,
        amount_in=10 * (10 ** 18),
        slippage_percent=0.5
    )

    # Print results
    print(pool_info)
    print(f'{"-" * 50}\n')
    print(f"pool_address: {pool_address[0]}")
    print(f"USDC_PRICE: ${pool_info['amount_out']:.3f}")
    print(f"MIN_USDC slippage 0.5% = {pool_info['min_amount_out']}")