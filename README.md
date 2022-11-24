
# -code-example

## попробовать запустить это:
### установка соендинения:
```
from amdi.binance.ws import Connection
callback=print
conn=Connection(callback)
await conn.connect()
```

### осуществеление подписок:
```
rkey_trades=await conn.sub_trades('BTC-ETH', agg=True)
rkey_updates=await conn.sub_orderbook('BTC-ETH')
rkey_ticker_chl=await conn.sub_tickers_chl('BTC-ETH')
```

### отмена подписок
```
await conn.unsub(rkey_trades, rkey_updates)

```
