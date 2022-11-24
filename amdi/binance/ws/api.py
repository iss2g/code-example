# py
import numpy as np

#from amdi.ws.constants import SERVICE
from amdi.ws import Api_base, Stream
from amdi.ws.constants import *
from amdi.ws.exceptions import UnknownMarket, InvalidParameterSet


'''
from amdi.binance.ws import Api | from amdi.ws.binance import Api
from amdi.ws.connection import Connection

####
*Api.update_basequote_map(basequote_map)

api=Api(**connection_params)	#connection_params include basequote_map
*api.update_basequote_map(basequote_map)
connection=Connection(api, callback)

*connection.update_basequote_map(basequote)

await connection.connect()

connection.update_basequote_map()


###
connection=Connection(Api, callback, **connection_params)


###
from amdi.binance.ws import connect | from amdi.binance import ws
conn=await ws.connect(callback, **connection_params)

###
from amdi.binance.ws import Connection		#alias for Connection_builder
conn=Connection(callback, **connection_params)
await conn.connect()

'''



class Sequence:
    def __init__(self, fr=0):
        self.fr = fr

    def next(self, step=1):
        self.fr = self.fr + step
        return self.fr
        

class Api(Api_base):
	chanel_next = Sequence(1000).next
	next_query_id = Sequence(10).next

	rtp_map = {
		'trade': 'sub_trades',
		'aggTrade': 'sub_trades',
		'kline': 'sub_ohlcv',
		'24hrMiniTicker': 'sub_tickers_c',
		'depthUpdate': 'sub_orderbook',
		'24hrTicker': 'sub_tickers_chl',
	}


	def __init__(self, **connection_params):
		super().__init__(**connection_params)
		self.wsurl = "wss://stream.binance.com:9443/ws/" + str(self.chanel_next())

		self.requests = {}  # rkey:request
		self.queries = {}  # id:{tp:ANY, 'rkeys':}

		self.failure_msg=None

	def join_basequote_exfrmt(self, base, quote):
		return f'{base}{quote}'.lower()

	def build_query(self, *requests_params):
		# (request_name, args, kwargs)
		query = {
			'method': 'SUBSCRIBE',
			'params': [],
			'id': self.next_query_id()
		}

		rkeys = []
		for request_name, args, kwargs in requests_params:
			adapter = self.adapters[request_name]
			rkey = adapter.get_rkey(*args, **kwargs)
			rkeys.append(rkey)
			request = adapter.build_request(*args, **kwargs)
			query['params'].append(request)

		self.queries[query['id']] = {'tp': SUB, 'rkeys': rkeys}
		self.requests.update(dict(zip(rkeys, query['params'])))

		return self.encode(query)

	def build_query_unsub(self, *rkeys):
		query = {
			'method': 'UNSUBSCRIBE',
			'params': [],
			'id': self.next_query_id()
		}
		for rkey in rkeys:
			query['params'].append(self.requests[rkey])

		self.queries[query['id']] = {
			'tp': UNSUB,
			'rkeys': rkeys
		}
		return self.encode(query)

	def parse_msg(self, tm, msg):
		msg_tp = self.identify_msg(msg)
		return getattr(self, 'parse_' + msg_tp.lower())(tm, msg)

	def identify_msg(self, msg):
		if isinstance(msg, dict):
			if msg.get('e'):
				return DATA

			elif 'result' in msg and 'id' in msg:
				query_id = msg['id']

				query_tp = self.queries[query_id]['tp']

				if query_tp == SUB:
					return SUCCESS

				elif query_tp == UNSUB:
					return UNSUB
			elif 'error' in msg  and 'id' in msg:
				return FAILURE

		elif isinstance(msg, list):
			if len(msg) > 0:
				isnt_data = sum([not part.get('e') for part in msg])
				if not isnt_data:
					return DATA
		raise UnexpectedMessage

	def parse_data(self, tm, msg):
		adapter = self.find_adapter(msg)
		return [{
			'tm': tm,
			**adapter.parse(tm, msg)
		}]

	def parse_success(self, tm, msg):
		query_id = msg['id']
		query_info = self.queries.pop(query_id)
		rkeys = query_info['rkeys']
		msgs = []
		for rkey in rkeys:
			msgs.append({
				'tm': tm,
				'kind': STREAM,
				'tp': SUCCESS,
				'rkey': rkey
			})
		return msgs

	def parse_unsub(self, tm, msg):
		query_id = msg['id']
		query_info = self.queries.pop(query_id)
		rkeys = query_info['rkeys']
		msgs = []
		for rkey in rkeys:
			self.requests.pop(rkey)
			msgs.append({
				'tm': tm,
				'kind': STREAM,
				'tp': UNSUB,
				'rkey': rkey
			})
		return msgs

	def parse_failure(self, tm, msg):
		"""
		{"error":{"code":2,"msg":"Invalid request: missing field `method` at line 4 column 1"},"id":3}
		{"error":{"code":4,"msg":"Too many subscriptions"},"id":1}
		"""
		query_id = msg['id']
		query_info = self.queries.pop(query_id)
		rkeys = query_info['rkeys']
		msgs = []
		
		failure=self.identify_failure_tp(msg)
	
		self.failure_msg=msg
		
		for rkey in rkeys:
			msgs.append({
				'tm':tm,
				'kind':STREAM,
				'tp':FAILURE,
				'failure':failure,
				'msg':msg,
				'rkey':rkey
				})
		return msgs		
		'''
		return [{
			'tm': tm,
			'kind': FAILURE,
			'tp': self.identify_failure_tp(msg),
			'msg': msg
		}]
		'''

	def identify_failure_tp(self, msg):
		error = msg['error']
		code = error['code']
		errmsg = error['msg']

		if code == 1:
			return 'unknown'  # //invalid value type

		if code == 2:
			return 'unknown'  # //invalid_request:
		if code == 3:
			return 'unknown'  # //invalid_json

		if code == 4:
			if errmsg == 'Too many subscriptions':
				return 'too_many_subscriptions'
			else:
				return 'unknown'
		return 'unknown'
#		
#	def parse_errex(self, tm, errex, action):
#		if self.failure_msg:
#			...
#			
#		else:
#			...
#		
#	
#		return [msg]
#		
##		if errex.reason=='Too many requests':
##			msg={
##				'tm':tm,
##				'kind':CLOSED,
##				'tp':OUT_OF_LIMITS,
##				'errex':errex,
##			}
##		else:
##			msg={
##				'tm':tm,
##				'kind':CLOSED,
##				'tp':UNKNOWN,
##				'errex':errex
##				}
##			
##	
##		return [msg]

	def find_adapter(self, msg):
		if isinstance(msg, dict):
			event_tp = msg['e']
		else:
			event_tp=msg[0]['e']
		return self.adapters[self.rtp_map[event_tp]]

	def parse_errex(self, tm, errex, action):
		...
		return super().parse_errex(self, tm, errex, action)

class SubOhlcv(Stream, Api):
	dtp = 'ohlcv'

	intervals_map = {
		'1m': '1m',
		'5m': '5m',
		'1d': '1d',
	}

	order = ['market', 'interval']

	# rkey_tmp=namedtuple(f'{cls.rtp.lower()}_{cls.dtp.lower()}', ['market', 'interval'])

	def build_request(self, market, interval='1m'):
		symbol = self.symbol_to_exfrmt(market)
		interval = self.intervals_map[interval]
		return f'{symbol}@kline_{interval}'

	def get_rkey(self, market, interval='1m'):
		return self.rkey(market, interval)

	def parse(self, tm, msg):
		kline_raw = msg['k']
		kline = {
			'T': kline_raw['t'],
			'O': float(kline_raw['o']),
			'H': float(kline_raw['h']),
			'L': float(kline_raw['l']),
			'C': float(kline_raw['c']),
			'QV': float(kline_raw['q']),
			'BV': float(kline_raw['v']),
			'T_close': kline_raw['T'],
			'trades_count': kline_raw['n'],
			'bv_buy': float(kline_raw['V']),
			'qv_buy': float(kline_raw['Q']),
			'closed': kline_raw['x'],
		}

		market = self.symbol_to_infrmt(msg['s'])
		interval = kline_raw['i']

		return {
			'kind': STREAM,
			'tp': UPDATE,
			'data': kline,
			'rkey': self.rkey(market, interval)
		}


class SubTrades(Stream, Api):
	dtp = TRADES
	order=['market', 'agg']
	def build_request(self, market, agg=False):
		symbol = self.symbol_to_exfrmt(market)
		if agg:
			return f'{symbol}@aggTrade'
		else:
			return f'{symbol}@trade'

	def get_rkey(self, market, agg=False):
		return self.rkey(market, agg)

	def parse(self, tm, msg):
		market = self.symbol_to_infrmt(msg['s'])
		agg = msg['e'] == 'aggTrade'

		if agg:
			trade = {
				'T': np.datetime64(msg['T'], 'ms'),
				'aid': msg['a'],
				'id': msg['f'],
				'id_last': msg['l'],
				'P': msg['p'],
				'V': msg['q'],
				'buyer_maker': msg['m'],
				'best_match': msg['M'],
				'T_event': msg['E'],
				'buyer_id': None,  #
				'seller_id': None,  #
				'V_details': None  #
			}
		else:
			trade = {
				'T': np.datetime64(msg['T'], 'ms'),
				'aid': None,  #
				'id': msg['t'],
				'id_last': msg['t'],
				'P': msg['p'],
				'V': msg['q'],
				'buyer_maker': msg['m'],
				'best_match': msg['M'],
				'T_event': msg['E'],
				'buyer_id': msg['b'],
				'seller_id': msg['a'],
				'V_details': None,  #
			}
		return {
			'kind': STREAM,
			'tp': UPDATE,
			'data': trade,
			'rkey': self.rkey(market, agg)
		}


class SubOrderbook(Stream, Api):
	dtp = ORDERBOOK
	order=['market', 'freq']
	def build_request(self, market, freq=100):
		symbol = self.symbol_to_exfrmt(market)

		if freq not in [100, 1000]:
			raise InvalidParameterSet

		if freq == 100:
			return f'{symbol}@depth@100ms'
		else:
			return f'{symbol}@depth'

	def get_rkey(self, market, freq=100):
		return self.rkey(market, None)


	def parse(self, tm, msg):
		symbol = msg['s']
		market = self.symbol_to_infrmt(symbol)

		orderbook_up = {
			'tm': np.datetime64(msg['E'], 'ms'),
			'id_start': msg['U'],
			'id': msg['u'],
			'bids': [[float(step[0]), float(step[1])] for step in msg['b']],
			'asks': [[float(step[0]), float(step[1])] for step in msg['a']],
			'received_at': tm
		}

		return {
			'kind': STREAM,
			'tp': UPDATE,
			'data': orderbook_up,
			'rkey': self.rkey(market, None)
		}


class SubTickers_C(Stream, Api):
	dtp = TICKERS_C
	stream_name = 'miniTicker'
	order=['market']
	def build_request(self, market=None):
		if market:
			symbol = self.symbol_to_exfrmt(market)
			return f'{symbol}@{self.stream_name}'
		else:
			return f'!{self.stream_name}@arr'

	def get_rkey(self, market=None):
		if market:
			return self.rkey(market)
		else:
			return self.rkey(ALL)

	def get_conflict_keys(self, market=None):
		if market:
			return (
				self.get_rkey(market),
				self.rkey(ALL)
			)
		else:
			return (
				self.get_rkey(market),
				self.rkey(ANY)
			)

	def parse(self, tm, msg):
		if isinstance(msg, dict):
			data = self.parse_one(tm, msg)
			rkey = self.rkey(data['market'])
		else:
			data = {}
			for ticker_raw in msg:
				ticker = self.parse_one(tm, ticker_raw)
				data[ticker['market']] = ticker
			rkey = self.rkey(ALL)
		return {
			'kind': STREAM,
			'tp': UPDATE,
			'data': data,
			'rkey': rkey
		}

	def parse_symbol(self, symbol):
		try:
			return self.symbol_to_infrmt(symbol)
		except UnknownMarket as unknown_market:
			return unknown_market

	def parse_one(self, tm, ticker):
		return {
			'market': self.parse_symbol(ticker['s']),
			'tm': np.datetime64(ticker['E'], 'ms'),
			'C': float(ticker['c'])
		}


class SubTickers_CHL(SubTickers_C, Stream, Api):
	dtp = TICKERS_CHL
	stream_name = 'ticker'

	def parse_one(self, tm, ticker):
		return {
			'market': self.parse_symbol(ticker['s']),
			'tm': np.datetime64(ticker['E'], 'ms'),
			'C': float(ticker['c']),
			'H': float(ticker['a']),
			'L': float(ticker['b'])
		}
		
		
		

	
		
		
		
		
		

