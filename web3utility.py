import os
import json
import statistics
from decimal import Decimal
from dotenv import load_dotenv
from typing import List, Dict, Union, Any
from web3 import Web3

load_dotenv("web3.env")

"""
Web3Utility クラス

このユーティリティクラスは、Web3ブロックチェーンの操作を簡素化し、開発効率を向上させます。

主な機能:
1. Web3接続管理: 簡潔な初期化とコントラクト設定
2. ガス最適化: 効率的なガス料金計算と推定
3. トークン操作: ERC20トークンの管理と操作
4. プール操作: Uniswap V3プールとの連携
5. トランザクション管理: 複数トランザクションの一括処理

使用例:
- スマートコントラクトとの対話
- トークン承認と転送
- 流動性プールの操作
- ガス料金の最適化
"""

class Web3Utility:
    def __init__(self, 
                 rpc_url: str = None, 
                 rpc_key: str = None,
                 chain: str = None, 
                 contract_address: str = None,
                 abi: list[dict] = None,
                 user_address: str = None):
        try:
            full_rpc_url = rpc_url.replace("choice_chain", chain) + rpc_key
            self.w3 = Web3(Web3.HTTPProvider(full_rpc_url))
            self.target_contract = self.w3.to_checksum_address(contract_address)
            self.abi = abi
            self.user_address = self.w3.to_checksum_address(user_address)
            self.contract = self.w3.eth.contract(address=self.target_contract, abi=abi)
            self.gas_fees = self.get_block_gas_fees()
            self.token_contract = None
            self.approve_tx = None
            
            if (self.w3.is_address(self.target_contract) 
                and self.w3.is_address(self.user_address) 
                and self.w3.is_connected()):
                print("Web3Utility initialized successfully.")
            else:    
                raise ConnectionError("Initialization failed. Check your parameters.")    
        except Exception as e:
            print(f"Input argument error for Web3Utility: {e}")

    def estimate_gas_limit(self, *args, function_name: str = None, value: int = None, contract: bool = True) -> int:
        if contract:
            contract_function = getattr(self.contract.functions, function_name)
        else:
            contract_function = getattr(self.token_contract.functions, function_name)
        try:
            if value is not None:
                estimated_gas = contract_function(*args).estimate_gas({"from": self.user_address, "value": value})
            else:    
                estimated_gas = contract_function(*args).estimate_gas({"from": self.user_address})
            return int(estimated_gas)
        except Exception as e:
            print(f"Function error in estimate_gas_limit: {e}")

    def get_block_gas_fees(self, 
                          blocks: int = 50, 
                          newest: str = "latest",
                          percentiles: List[int] = [25, 50, 75], 
                          reward_percentile: int = 50, 
                          max_fee_multiplier: float = 2,
                          reward_multiplier: float = 1) -> dict:
        block_fee_data = self.w3.eth.fee_history(block_count=blocks, newest_block=newest, reward_percentiles=percentiles)
        base_fee_avg = statistics.mean(block_fee_data["baseFeePerGas"][:-1])
        priority_fee_median = statistics.median(fee[percentiles.index(reward_percentile)] for fee in block_fee_data["reward"])

        max_fee = (base_fee_avg * max_fee_multiplier) + priority_fee_median * reward_multiplier
        return {
            'maxFeePerGas': int(max_fee),
            'priorityFeePerGasMedian': int(priority_fee_median),
            'baseFeeAvg': int(base_fee_avg),
        }

    def decode(self, data: Union[str, bytes], types: List[str]) -> List[Any]:
        if isinstance(data, bytes):
            byte_data = data
        else:
            clean_data = data[2:] if data.startswith('0x') else data
            byte_data = bytes.fromhex(clean_data)
        
        decoded = self.w3.codec.decode(types, byte_data)
        return list(decoded)

    def encode(self, values: List[Any], types: List[str]) -> str:
        encoded = self.w3.codec.encode(types, values)
        hex_data = '0x' + encoded.hex()
        return hex_data
    
    def load_erc20_contract(self, contract: str = None):
        with open("Abi/token_basics_abi.json", mode="r") as file:
            self.basics_token_abi = json.load(file)
        contract = self.w3.to_checksum_address(contract)
        self.token_contract = self.w3.eth.contract(address=contract, abi=self.basics_token_abi)   
        return self.token_contract 
    
    def token_approve(self,
                     target_contract: str = None, 
                     value: int = 0): 
        self.approve_gaslimit = self.estimate_gas_limit(target_contract, value, function_name="approve", contract=False)
        self.approve_tx = self.token_contract.functions.approve(target_contract, value).build_transaction(
            self.build_tx_params(gas_limit=self.approve_gaslimit)
        )
        return self.approve_tx 
    
    def load_pool_contract(self, contract: str = None):
        with open("Dapps/UniswapAbi/UniswapV3_pool_abi.json", mode="r") as file:
            self.uniV3_pool_abi = json.load(file)
        contract = self.w3.to_checksum_address(contract)
        self.pool_contract = self.w3.eth.contract(address=contract, abi=self.uniV3_pool_abi)
        return self.pool_contract
    
    def simple_slippage(self,
                       pool_address: str = None,
                       path: bool = True,
                       amount_in: int = 0,
                       slippage_percent: float = 0.5) -> dict:
        try:
            pool = self.load_pool_contract(pool_address)
            
            slot0_info = pool.functions.slot0().call()
            sqrt_price = Decimal(slot0_info[0]) / Decimal(2 ** 96)
            price = sqrt_price * sqrt_price
            
            token0 = pool.functions.token0().call()
            token1 = pool.functions.token1().call()
            decimal0 = self.load_erc20_contract(token0).functions.decimals().call()
            decimal1 = self.load_erc20_contract(token1).functions.decimals().call()
            
            price = price * Decimal(10 ** (decimal0 - decimal1))
           
            if path:
                actual_price = price
                decimals_out = decimal1
                amount_in = amount_in / (10 ** decimal0)
            else:
                actual_price = Decimal(1) / price
                decimals_out = decimal0
                amount_in = amount_in / (10 ** decimal1) 

            if amount_in != 0:
                amount_out = Decimal(actual_price) * Decimal(amount_in)
                min_amount = amount_out * Decimal((100 - slippage_percent)) / 100
                min_amount_decimal = int(min_amount * (10 ** decimals_out))
            else:
                amount_out = Decimal(actual_price)
                min_amount = actual_price * Decimal((100 - slippage_percent)) / 100
                min_amount_decimal = int(min_amount * (10 ** decimals_out))

            return {
                "min_amount_out": min_amount_decimal,
                "amount_out": float(amount_out),
                "min_actual_amount": float(min_amount),
                "token0": token0,
                "token1": token1,
                "current_tick": slot0_info[1],
                "sqrt_price_x96": slot0_info[0],
                "decimals_out": decimals_out
            }
        except Exception as e:
            print(f"Error in simple_slippage: {e}")
            return None
    
    def build_tx_params(self, 
                       gas_limit: int = 21000,
                       value: int = 0,
                       extra_params: dict = None) -> dict:          
        tx_data = {
            'from': self.user_address,
            'gas': gas_limit,
            'maxFeePerGas': self.gas_fees['maxFeePerGas'],
            'maxPriorityFeePerGas': self.gas_fees['priorityFeePerGasMedian'],
            'nonce': self.w3.eth.get_transaction_count(self.user_address),
            'value': value,
            'type': '0x2',
            'chainId': self.w3.eth.chain_id,
        }
        if extra_params:
            tx_data.update(extra_params)
        return tx_data
    
    def send_multiple_tx(self, txs: list, private_key: str, basicGas: bool = True):
        for i, tx in enumerate(txs):
            try:
                print(f"\nExecuting transaction {i+1}/{len(txs)}")
                tx["nonce"] = self.w3.eth._get_transaction_count(self.user_address)
                if basicGas:
                    gasfees = self.get_block_gas_fees()
                    tx["maxFeePerGas"] = gasfees["maxFeePerGas"]
                    tx["maxPriorityFeePerGas"] = gasfees["priorityFeePerGasMedian"]
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"Transaction Hash: {tx_hash.hex()}")
                
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if tx_receipt['status'] == 1:
                    print(f"Transaction {i+1} successful!")
                    continue  
                else:
                    print(f"Transaction {i+1} failed!")
                    return False  
                    
            except Exception as e:
                print(f"Transaction {i+1} Error: {e}")
                return False
        print("All transactions completed successfully!")               
        return True 

    def get_token_info(self, token_address: str) -> dict:
        """
        トークンの基本情報（名前、シンボル、デシマル、総供給量、ユーザー残高）を取得します
        """
        token = self.load_erc20_contract(token_address)
        try:
            return {
                'name': token.functions.name().call(),
                'symbol': token.functions.symbol().call(),
                'decimals': token.functions.decimals().call(),
                'total_supply': token.functions.totalSupply().call(),
                'balance': token.functions.balanceOf(self.user_address).call()
            }
        except Exception as e:
            print(f"Error getting token info: {e}")
            return None