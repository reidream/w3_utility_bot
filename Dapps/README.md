# Uniswap V3 マルチコールデータ解析・実行ユーティリティ

## トランザクションの解析例

### 1. シンプルなスワップ（WETH→USDC）

```
Input Data:
0x5ae401dc00000000000000000000000000000000000000000000000000000000671d2a22...

=== デコード結果 ===
Function: multicall with exactInputSingle
Parameters:
- TokenIn:  WETH (0x82aF494...)
- TokenOut: USDC (0xaf88d06...)
- Fee: 0.05% (500)
- Amount: 5.0 WETH
- MinOut: 12,299.834718 USDC
```

### 2. 複合トランザクション（USDC→ETH）

```
Input Data:
0xac9650d8000000000000000000000000000000000000000000000000000000000000002...

=== デコード結果 ===
Function: multicall with:
1. exactInput:
   - Input: 128.307587 USDC → WETH
   - MinOut: 0.050820617030482392 WETH

2. unwrapWETH9:
   - Amount: 0.050820617030482392 ETH
   - To: 0x4c2Ed4...
```

## 使用方法

### デコード機能

```python
# サンプル1のデータ
test_input_data_1 = '0x5ae401dc00000000000000000000000000000000000000000000000000000000671d2a22...'

# サンプル2のデータ
test_input_data_2 = '0xac9650d800000000000000000000000000000000000000000000000000000000000000200...'

# デコード実行
result = uni_bot.decode_multicall(test_input_data_1)
```

### スワップ実行

```python
# パラメータ設定
params = {
    'path': token_path,
    'recipient': youraddress
    'amountIn': amount,
    'amountOutMinimum': min_amount
}

# 関数エンコード
encoded_exactInput = uni_bot.contract.encodeABI(
    fn_name="exactInput",
    args=[params]
)
encoded_unwrapWETH9 = uni_bot.contract.encodeABI(
    fn_name="unwrapWETH9",
    args=[min_amount]
)

# マルチコール実行
multicall_data = [
    encoded_exactInput,
    encoded_unwrapWETH9
]
```

## 重要なパラメータ

### Arbitrum のコントラクトアドレス

- USDC: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`
- WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`

### 手数料設定

| プール | 用途       | 手数料率 |
| ------ | ---------- | -------- |
| 100    | ステーブル | 0.01%    |
| 500    | ETH/USDC   | 0.05%    |
| 3000   | 一般       | 0.3%     |
| 10000  | 高変動     | 1%       |

このツールを使用することで、Uniswap のマルチコールトランザクションを簡単に解析・実行できます。サンプルデータの解析結果から、トークンの流れや設定された条件を把握して実際に自分で multicall 関数利用できます。

## [test_multicall_unibot.py](test_multicall_unibot.py)

処理の流れ

USDC から WETH へのスワップパスを設定（0.05%手数料プール使用）
スワップ金額を 0.01 USDC（1000 units）に設定
exactInput 関数でスワップを実行
unwrapWETH9 関数で受け取った WETH を即座に ETH へ変換
マルチコールで両操作を一つのトランザクションにまとめる
ガス代を最適化して実行
