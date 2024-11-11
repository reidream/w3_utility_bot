import os
from dotenv import load_dotenv
from Dapps.uniswap_utility import Uniutility

# 環境変数の読み込みとUniswapユーティリティの初期化
load_dotenv('web3.env')
uni_bot = Uniutility(
    rpc_url=os.getenv("INFURA_URL"),
    rpc_key=os.getenv("RPC_KEY"),
    chain="base",
    contract_address="0x2626664c2603336E57B271c5C0b26F421741e481",
    user_address=os.getenv("ADDRESS")
)

# トークンアドレスの設定（Base チェーン上のアドレス）
USDC, WETH, DAI = (
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "0x4200000000000000000000000000000000000006",
    "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
)
amount = 10000  # スワップする金額（USDC/DAIの量）0.01ドル
tx_list = []

# USDCとDAIのアプルーブ処理
for token in [USDC, DAI]:
    uni_bot.load_erc20_contract(token)
    tx = uni_bot.token_approve(uni_bot.target_contract, amount)
    uni_bot.send_multiple_tx([tx], os.getenv("KEY"))

# スワップデータの作成と実行
for token in [USDC, DAI]:
    # プールアドレスの取得（fee=500はUniswapV3の0.05%手数料tier）
    pool = uni_bot.get_pool_address(WETH, token, [500])[0]
    data = uni_bot.exact_input(
        path=[token, WETH],
        path_forward=False,
        fee=500,
        amount_in=amount,
        slippage=0.5,  # スリッページ許容値 0.5%
        recipient=uni_bot.user_address,
        pool_address=pool
    )
    
    # マルチコールトランザクションの構築
    multicall = uni_bot.multicall([data["encoded_exactInput"]])
    tx = uni_bot.contract.functions.multicall(
        [multicall["encoded_multicall"]]
    ).build_transaction(
        uni_bot.build_tx_params(gas_limit=multicall["gaslimit"])
    )
    tx_list.append(tx)

# すべてのトランザクションを一括実行
uni_bot.send_multiple_tx([tx_list[0], tx_list[1]], os.getenv("KEY"))