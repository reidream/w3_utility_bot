import os
import time
import json
from dotenv import load_dotenv
from web3utility import Web3Utility
load_dotenv('web3.env')
with open('ape_abi.json', mode='r') as file:
    ape_abi = json.load(file)

ape_bot = Web3Utility(
    rpc_url='https://choice_chain.calderachain.xyz/http',
    rpc_key='',
    chain='apechain',
    contract_address="0xe4103e80c967f58591a1d7cA443ed7E392FeD862",
    abi=ape_abi,
    user_address=os.getenv('ADDRESS')
)
# make sendParam, _fee, _refundAddress
# sendParam
dstEid = 30110 #arb uint32
to = ape_bot.w3.to_bytes(hexstr='0x8bed0eCED8b89541AA5A95357fDd589aCF24579C').rjust(32, b'\0') #bytes32
amountLD = int(0.1 * (10 ** 18)) #uint256
minAmountLD = int(amountLD * 0.99) #uint256
extraOptions = ape_bot.w3.to_bytes(hexstr='0x0003010011010000000000000000000000000000fde8') #bytes
composeMsg = b'' #bytes
oftCmd = b'' #bytes
sendParam = (dstEid,
            to,
            amountLD,
            minAmountLD,
            extraOptions,
            composeMsg,
            oftCmd
            ) #tuple
# _fee
lzTokenFee = False
_fee = ape_bot.contract.functions.quoteSend(sendParam, lzTokenFee).call()
# _refundAddress
_refundAddress = ape_bot.user_address

# make gas limit and test tx
gas_limit = ape_bot.estimate_gas_limit(sendParam,
                                      _fee,
                                      _refundAddress,
                                      function_name='send',
                                      value=(amountLD + _fee[0]))
#print(gas_limit)
gas_fees = ape_bot.get_block_gas_fees()

tx = ape_bot.contract.functions.send(sendParam,
                                     _fee,
                                     _refundAddress
                                     ).build_transaction({
                                    'from': ape_bot.user_address,
                                    'gas': gas_limit,
                                    'maxFeePerGas': gas_fees['maxFeePerGas'],
                                    'maxPriorityFeePerGas': gas_fees['priorityFeePerGasMedian'],
                                    'nonce': ape_bot.w3.eth.get_transaction_count(ape_bot.user_address),
                                    'value': (amountLD + _fee[0]),
                                    'type': '0x2',
                                    'chainId': ape_bot.w3.eth.chain_id,
                                    })

# try to send tx
try:
    signed_tx = ape_bot.w3.eth.account.sign_transaction(tx, os.getenv('KEY'))
    tx_hash = ape_bot.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = ape_bot.w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Tx sent. Hash: {tx_hash.hex()}")
except Exception as e:
    print(f"Transaction error: {e}")    

tx_receipt = ape_bot.w3.eth.wait_for_transaction_receipt(tx_hash)