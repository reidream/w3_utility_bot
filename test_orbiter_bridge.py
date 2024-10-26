import os 
import json
from dotenv import load_dotenv
from web3utility import Web3Utility

# 環境変数の読み込み
load_dotenv("web3.env")

# コントラクトアドレスとネットワーク設定
ORBITER_BASE_CONTRACT = "0x13e46b2a3f8512ed4682a8fb8b560589fe3c2172"
# 保有トークンの多いコントラクトアドレス利用　基本BRIDGE1
ORBITER_BRIDGE1_CONTRACT = "0x80C67432656d59144cEFf962E8fAF8926599bCF8"
ORBITER_BRIDGE2_CONTRACT = "0xE4eDb277e41dc89aB076a1F049f4a3EfA700bCE8"

CHAIN = "base"
RPC_URL = os.getenv("INFURA_URL")
RPC_KEY = os.getenv("RPC_KEY")
USER_ADDRESS = os.getenv("ADDRESS")

# ABIの読み込み
with open("orbiter_abi.json", mode="r") as file:
    ORBITER_ABI = json.load(file)

# Web3Utilityインスタンスの作成
orbiter_base = Web3Utility(
    rpc_url=RPC_URL,
    rpc_key=RPC_KEY, 
    chain=CHAIN, 
    contract_address=ORBITER_BASE_CONTRACT,
    abi=ORBITER_ABI,
    user_address=USER_ADDRESS
)

# Orbiter転送のパラメータ設定
ORBITER_ID = 9002  # 9002 は Arbitrum への転送を示す
AMOUNT_ETH = 0.00047
amount_wei = orbiter_base.w3.to_wei(AMOUNT_ETH, 'ether') + ORBITER_ID


# 転送先情報
types = ["address"] # type address list
TO_ADDRESS = [orbiter_base.user_address]  # values list 自分のアドレス

# Orbiter用のデータ生成
byte_data = orbiter_base.encode(values=TO_ADDRESS ,types=types)

# ガス料金の取得
gas_fees = orbiter_base.get_block_gas_fees()

# ガスリミットの推定
gas_limit = orbiter_base.estimate_gas_limit(
    ORBITER_BRIDGE1_CONTRACT, 
    byte_data, 
    function_name='transfer', 
    value=amount_wei
)

# トランザクションの構築
tx = orbiter_base.contract.functions.transfer(
    ORBITER_BRIDGE2_CONTRACT, 
    byte_data
).build_transaction({
    'from': orbiter_base.user_address,
    'gas': gas_limit,
    'maxFeePerGas': gas_fees['maxFeePerGas'],
    'maxPriorityFeePerGas': gas_fees['priorityFeePerGasMedian'],
    'nonce': orbiter_base.w3.eth.get_transaction_count(orbiter_base.user_address),
    'value': amount_wei,
    'type': '0x2',
    'chainId': orbiter_base.w3.eth.chain_id
})
print(tx)

#トランザクションの署名と送信
signed_tx = orbiter_base.w3.eth.account.sign_transaction(tx, os.getenv("KEY"))
tx_hash = orbiter_base.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
print(f"トランザクション送信完了。Hash: {tx_hash.hex()}")

# トランザクション確認の待機
tx_receipt = orbiter_base.w3.eth.wait_for_transaction_receipt(tx_hash)

# 結果の表示
print(f"トランザクション確認完了。ブロック番号: {tx_receipt['blockNumber']}")
print(f"トランザクションインデックス: {tx_receipt['transactionIndex']}")
print(f"合計L2ガス使用量: {tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']}")
print(f"このトランザクションのガス使用量: {tx_receipt['gasUsed']}")
print(f"有効ガス価格: {tx_receipt['effectiveGasPrice']}")
