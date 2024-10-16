# Web3Utility

Web3Utility は、Ethereum 互換ブロックチェーンとのインタラクションを簡素化する Python クラスです。ガス料金の最適化、データのエンコード/デコード、Web3bot 開発の基礎を class の呼び出しにより操作を時短化できます、また一番の目的はここからの追加でいろんな機能を付け加えることにより高機能のカスタマイズ bot を目指しています。

## 現在の主な機能

1. **動的ガス料金最適化**: `get_block_gas_fees()` メソッドで最適なガス料金を計算
2. **ABI エンコード/デコード**: `decode()` と `encode()` メソッドでデータの変換を簡易化
3. **ガスリミット推定**: `estimate_gas_limit()` で適切なガスリミットを推定
4. **ブリッジ操作サポート**: Stargate, Orbiter などのブリッジ操作をサポート

## 使用方法

### 初期化

```python
web3_util = Web3Utility(rpc_url, rpc_key, chain, contract_address, abi, user_address)
gas_fees = web3_util.get_block_gas_fees()
gas_limit = web3_util.estimate_gas_limit(*args, function_name="function_name", value=amount)
decoded_data = web3_util.decode(encoded_data, types)
encoded_data = web3_util.encode(values, types)
# Stargate
stg_base = Web3Utility(...)
tx = stg_base.contract.functions.send(...).build_transaction({...})

# Orbiter
orbiter_base = Web3Utility(...)
tx = orbiter_base.contract.functions.transfer(...).build_transaction({...})
```

## メリット

bot 作成の短縮: 複雑な Web3 基本操作を簡易化
ガスコスト最適化: 動的なガス料金計算で取引コストを最小化
柔軟性: コードのアップデート可能
安全性: エラーハンドリングと適切な型チェックを内蔵

## テスト

[test_orbiter_bridge.py](test_orbiter_bridge.py) \
[test_stargate_bridge.py](test_stargate_bridge.py)\
こちらで bridge テストできます。
