import os
import statistics
from dotenv import load_dotenv
from typing import List, Dict, Union, Any
from web3 import Web3
load_dotenv("web3.env")

"""
Web3Utility クラス

このクラスは、Web3 ブロックチェーンとのインタラクションを大幅に簡素化し、開発効率を向上させます。
主な利点は以下の通りです：

1. 簡単な初期化: 複雑な Web3 接続とコントラクトのセットアップを簡易化
2. ガス最適化: 正確なガス料金推定機能により、取引コストを最小限に抑制
3. 動的なガス戦略: リアルタイムのブロックチェーンガス情報取得で、常に最適なガス料金を設定可能
4. データ処理の効率化: 内蔵のABIエンコード/デコード機能で、複雑なデータ変換を簡素化

このクラスを使用することで、開発時間の短縮、コードの可読性向上に役立ち、また機能のアップデートの基盤として役立ちます。
＊今後利便性アップ機能は追加していく予定です。

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
            self.user_address = self.w3.to_checksum_address(user_address)
            self.contract = self.w3.eth.contract(address=self.target_contract, abi=abi)
             
            if (self.w3.is_address(self.target_contract) 
                and self.w3.is_address(self.user_address) 
                and self.w3.is_connected()):
                print("Web3Utility initialized successfully.")
            else:    
                raise ConnectionError("Initialization failed. Check your parameters.")    
        except Exception as e:
            print(f"Input argument error for Web3Utility: {e}") 

    def estimate_gas_limit(self, *args, function_name: str = None, value: int = None) -> int:
        contract_function = getattr(self.contract.functions, function_name)
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


