# py

#
ALL = 'ALL'
ANY = 'ANY'

# requests types:
GET = 'GET'
SUB = 'SUB'

# data types

OHLCV = 'OHLCV'
TRADES = 'TRADES'
ORDERBOOK = 'ORDERBOOK'
TICKERS_C = 'TICKERS_C'
TICKERS_CHL = 'TICKERS_CHL'

# kinds:
SERVICE = 'SERVICE'
STREAM = 'STREAM'
RESPONSE = 'RESPONSE'
CLOSED = 'CLOSED'

PARSE_ERROR = 'PARSE_ERROR'
DECODE_ERROR = 'DECODE_ERROR'

# msg types:
# service
GREETING = 'GREETING'
PARTING = 'PARTING'
PING = 'PING'
PONG = 'PONG'
HEARTBEAT = 'HEARTBEAT'
INFO = 'INFO'
# UNKNOWN_SYMBOL='UNKNOWN_SYMBOL'	#pass basequote_map

# STREAM/GET_RESPONSE
SUCCESS = 'SUCCESS'  # STREAM ONLY
FAILURE = 'FAILURE'
UPDATE = 'UPDATE'  # STREAM ONLY
UNSUB = 'UNSUB'  # STREAM ONLY
SNAPSHOT = 'SNAPSHOT'  # STREAM/GET_RESPONSE
DATA = 'DATA'
# ERROR='ERROR'		#not parsing ERROR

# STREAM/GET_RESPONSE|FAILURE|REASON
INVALID_PARAMS = 'INVALID_PARAMS'
INVALID_MARKET = 'INVALID_MARKET'
OUT_OF_LIMITS = 'OUT_OF_FREQ_LIMITS'  # превышение частоты запросов
OUT_OF_QNT_LIMITS = 'OUT_OF_QNT_LIMITS'  # превышение максимального числа подпиок вообще
OUT_OF_FREQ_LIMITS = 'OUT_OF_FREQ_LIMITS_MSG'  # превышение частоты сообений

# ERROR|REASON
UNKNOWN_SYMBOL = 'UNKNOWN_SYMBOL'

# CLOSED
OK='OK'


LIFE_EXPIRED = 'LIFE_EXPIRED'  # //соендинение проработало какое-то известное время после которого оно должно было быть сброшено
# // binance 24h, bittrex возмоно 100m

OUT_OF_LIMITS = 'OUT_OF_FREQ_LIMITS'  # //вызод за пределы ограничение частот запросов/подписок
OUT_OF_QNT_LIMITS = 'OUT_OF_QNT_LIMITS'  # //выход за пределы максимального числа запросов/активных подписок
OUT_OF_FREQ_LIMITS_MSG = 'OUT_OF_FREQ_LIMITS_MSG'  # //выход за пределы ограничения частот отправлемых сообщений
OUT_OF_FREQ_LIMITS_CONN = 'OUT_OF_FREQ_LIMITS_CONN'  # //выход за пределы частоты открытия соендинений
OUT_OF_QNT_LIMITS_CONN = 'OUT_OF_QNT_LIMITS_CONN'  # //выход за пределы максимального колличетва открытых соендинений

INVALID_MSG_WAS_SENT = 'INVALID_MSG_WAS_SENT'  # //соендинение оборвано, так как было отправлено недействительное сообщение/запрос

ACTIVATION_TIMEOUT = 'ACTIVATION_TIMEOUT'  # //соендинение было оборвано, так как после открытия не последдовало запросов.
PONG_TIMEOUT = 'PONG_TIMEOUT'  # //соендинение сброшено так как вовремя не получело ответный PONG
# //такое может быть когда, интернет соендинение ненадолго пропало
# //потом появилось, и в это время не был отправлен pong
SILENT_TIMEOUT = 'SILENT_TIMEOUT'  # //соендинение разорвано самостоятельно так как от обменика не было получено в течении определенного времени
# никакх сообщениий, в том числе ответного pong

UNKNOWN = 'UNKNOWN'

'''
AUTH_FAILURE


'''

