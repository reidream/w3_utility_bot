import os
import json
from dotenv import load_dotenv
from web3utility import Web3Utility

# 環境変数の読み込み
load_dotenv('web3.env')

# 定数
STARGATE_BASE_POOLNATIVE_SOL = "0xdc181Bd607330aeeBEF6ea62e03e5e1Fb4B6F7C7"
CHAIN = "base"
RPC_URL = os.getenv("INFURA_URL")
RPC_KEY = os.getenv("RPC_KEY")
USER_ADDRESS = os.getenv("ADDRESS")

# Stargate Base ABIの読み込み
with open("stargate_base_abi.json", mode="r") as file:
    STARGATE_BASE_ABI = json.load(file)

# Web3Utilityの初期化
stg_base = Web3Utility(
    rpc_url=RPC_URL,
    rpc_key=RPC_KEY,
    chain=CHAIN,
    contract_address=STARGATE_BASE_POOLNATIVE_SOL,
    abi=STARGATE_BASE_ABI,
    user_address=USER_ADDRESS
)

# Layer ZeroとStargateのID
LZ_STG_ID = 30000
STG_ARB_ID = 110
DESTINATION_EID = LZ_STG_ID + STG_ARB_ID

# トランザクションパラメータの準備
to_address = stg_base.w3.to_bytes(hexstr=stg_base.user_address).rjust(32, b"\0")  # 32 bytes
amount_ld = stg_base.w3.to_wei(0.00002, 'ether')  # uint256
min_amount_ld = int(amount_ld * 0.98)  # uint256
extra_options = b''  # bytes
compose_msg = b''  # bytes
oft_cmd = b'\x01'  # bytes (b'' = fast speed, b'\x01' = normal speed)

# 送信パラメータタプルの作成
send_params = (
    DESTINATION_EID,
    to_address,
    amount_ld,
    min_amount_ld,
    extra_options,
    compose_msg,
    oft_cmd
)

# 送信手数料の見積もり
use_lz = False
native_fee = stg_base.contract.functions.quoteSend(send_params, use_lz).call()  # tuple(uint256, uint256)
refund_address = stg_base.user_address  # address

# ガスリミットと手数料の推定
gas_limit = stg_base.estimate_gas_limit(
    send_params,
    native_fee,
    refund_address,
    function_name="send",
    value=(amount_ld + native_fee[0])
)
gas_fees = stg_base.get_block_gas_fees()

# トランザクションの作成
tx = stg_base.contract.functions.send(
    send_params,
    native_fee,
    refund_address
).build_transaction({
    'from': stg_base.user_address,
    'gas': gas_limit,
    'maxFeePerGas': gas_fees['maxFeePerGas'],
    'maxPriorityFeePerGas': gas_fees['priorityFeePerGasMedian'],
    'nonce': stg_base.w3.eth.get_transaction_count(stg_base.user_address),
    'value': (amount_ld + native_fee[0]),
    'type': '0x2',
    'chainId': stg_base.w3.eth.chain_id,
})

# トランザクションの署名と送信
try:
    signed_tx = stg_base.w3.eth.account.sign_transaction(tx, os.getenv('KEY'))
    tx_hash = stg_base.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"トランザクションが送信されました。Hash: {tx_hash.hex()}")
except Exception as e:
    print(f"トランザクション送信エラー:{e}")    

# トランザクションレシートの待機
tx_receipt = stg_base.w3.eth.wait_for_transaction_receipt(tx_hash)

# 結果の表示
print(f"トランザクションが確認されました。Block number: {tx_receipt['blockNumber']}")
print(f"Transaction index: {tx_receipt['transactionIndex']}")
print(f"Total Layer 2 gas fee: {tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']}")
print(f"このトランザクションのgas used: {tx_receipt['gasUsed']}")
print(f"Effective gas price: {tx_receipt['effectiveGasPrice']}")