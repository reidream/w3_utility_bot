import os
from dotenv import load_dotenv
from uniswap_utility import Uniutility

# 環境変数の読み込み
load_dotenv('web3.env')

# 設定定数
CHAIN = "arbitrum"
RPC_URL = os.getenv("INFURA_URL")
RPC_KEY = os.getenv("RPC_KEY")
USER_ADDRESS = os.getenv("ADDRESS")

"""
Uniswap V3のマルチコール機能を使用したスワップトランザクション実行スクリプト
"""

# Uniswap Utilityの初期化
uni_bot = Uniutility(
   rpc_url=RPC_URL,
   rpc_key=RPC_KEY,
   chain=CHAIN,  
   user_address=USER_ADDRESS
)

# トークンアドレス定義
USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"

# Uniswap V3の手数料率（Fee Tier）
# 0.01% = 100   : 安定コインペアに最適（例：USDC/USDT）
# 0.05% = 500   : 安定コインとの取引に推奨（例：ETH/USDC）
# 0.3%  = 3000  : 一般的な取引ペアのデフォルト値
# 1%    = 10000 : ボラティリティの高いペアに使用（例：特殊なトークン）
fee = 500  # ETH/USDCペアには0.05%を使用

# Call #1: exactInput関数のエンコード
byte_usdc = uni_bot.w3.to_bytes(hexstr=USDC)
byte_fee = fee.to_bytes(3, 'big')
byte_weth = uni_bot.w3.to_bytes(hexstr=WETH)
data = byte_usdc + byte_fee + byte_weth

params = {
   'path': data,
   'recipient': '0x8bed0eCED8b89541AA5A95357fDd589aCF24579C',
   'amountIn': 1000,  # 0.01 USDC
   'amountOutMinimum': 0  # テスト用に最小出力額を0に設定
}

encoded_exactInput = uni_bot.contract.encodeABI(fn_name="exactInput", args=[params])

# Call #2: unwrapWETH9関数のエンコード
encoded_unwrapWETH9 = uni_bot.contract.encodeABI(fn_name="unwrapWETH9", args=[params["amountOutMinimum"]])

# マルチコールデータの作成
multicall_data = [encoded_exactInput, encoded_unwrapWETH9]
print(multicall_data)

# ガスリミットとガス料金の取得
gaslimit = uni_bot.estimate_gas_limit(multicall_data, function_name="multicall")
gasFees = uni_bot.get_block_gas_fees()

# トランザクションの構築
tx = uni_bot.contract.functions.multicall(multicall_data).build_transaction({
   'from': uni_bot.user_address,
   'gas': gaslimit,
   'maxFeePerGas': gasFees['maxFeePerGas'],
   'maxPriorityFeePerGas': gasFees['priorityFeePerGasMedian'],
   'nonce': uni_bot.w3.eth.get_transaction_count(uni_bot.user_address),
   'value': 0,
   'type': '0x2',
   'chainId': uni_bot.w3.eth.chain_id
})

# # トランザクションの署名と送信
# signed_tx = uni_bot.w3.eth.account.sign_transaction(tx, os.getenv("KEY"))
# tx_hash = uni_bot.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
# print(f"トランザクション送信完了 | Hash: {tx_hash.hex()}")

# # トランザクション確認の待機
# tx_receipt = uni_bot.w3.eth.wait_for_transaction_receipt(tx_hash)

# # 実行結果の表示
# print("\nトランザクション実行結果")
# print(f"ブロック番号: {tx_receipt['blockNumber']}")
# print(f"トランザクションインデックス: {tx_receipt['transactionIndex']}")
# print(f"合計L2ガス使用量: {tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']} wei")
# print(f"ガス使用量: {tx_receipt['gasUsed']}")
# print(f"有効ガス価格: {tx_receipt['effectiveGasPrice']} wei")

