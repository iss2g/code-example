# py
import asyncio
import json
import time
from collections import namedtuple
from inspect import iscoroutinefunction
import websockets

from .constants import *
from .exceptions import *


# from .exceptions import *
# from .constants import *


class Sequence:
    def __init__(self, fr=0):
        self.fr = fr

    def next(self, step=1):
        self.fr = self.fr + step
        return self.fr


def as_async(func):
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


class Api_base:
    '''
    :param **prms:
        see below
    :Keyword Arguments:
        *basequote_map:
            type: dict		//{symbol1:(base, quote), ...}
            //ключ - рынок в формате представленном на обменнике
            //значение - кортеж содержащий base и quote для этого рынка

        *ignore_greeting:
            type: Bool	//default True
        *ignore_heartbeat:
            type: Bool	//default True
        *ignore_ping
            type: Bool	//default True
        *ignore_success
            type: Bool	//default False
        *ignore_pong


        *engine:
            type: websockets_like	//default websockets
            //может быть полезно изменить websockets для некоторых обмеников
            //с которыми websockets не может нормально общаться на уровне протокола
            //

        *timeout_silence:
            type: int|float	//in seconds
            //время отсутвия сообщений через которое будет послаться
            //ping.


        *timeout:
            type: int|float	//in seconds
            //период отсутсвия сообщений, в том числе сообщений которые
            //обрабатываются "под капотом" engine, через который соендинение
            //будет разорвано.

         *auth:
            type:Any	//default None
            //что-то для осуществления аутентификации
            //порядок которой прописан в Api.
            //Api должен уметь это применить в методе "get_ws_options"
            //-in url
            //-in headers
            //-in query

         **connect_params:
            see websockets.connect
        ;

    '''

    pingpong = False  		#// если обменик присылает ping на который необходимо ответить
			    #// после того как ping msg будет распарсен
			    #// {'send_it':pong_query}
			    #// api распарсив сообщение

    regular_ping = 0  		#// время через которое на обменик нужно регулярно слать ping
			    	#// для поддержания жизни соендинения.
			    	#// будет запущена корутина которая будет слать к обменику ping

    autoTracking = True    # //True - engine сам отслеживает, то что сообщения приходят
			    # //сам пингует сервер и разрывает соендинение если
			    # //не получает в течении timeout ответов.
			    # //если передано False, будет запущена
			    # //корутина отслеживающая время последнего сообщения
			    # //и если сообщений долго нет, будет пинговать сервер
			    # //и разрывать соендинение в случае неуспеха.
			    # //для этого в Api должен быть реализован метод
			    # //"build_ping_query" и метод для парсинга 		
			    # // пришедшедшего pong	

    timeout_silence = 20  	#// сколько секунд без сообщений должно пройти для того чтобы
			   	#// послать обменику сообщение с целью получения како-го сообщения.
			    	#// тоже что и параметр ping_interval в webscokets.connect

    timeout = 60 * 2  	 #// время через которое соендинение будет разорвано, если не
		   	 #// соендинение не получало никаких сообщений
		   	 #// тоже что и параметр ping_timeout в webscokets.connect()

    lifetime = 0  	#// время после которого UNKNOWN - причина закрытия соендинения
    			#// будет интерпретироваться как LIFE_EXPIRED

    ignore_greeting = True
    ignore_heartbeat = True
    ignore_ping = True
    ignore_pong = True
    ignore_success = False

    basequote_map = None
    markets_aliases = None

    auth = None

    auth_tp = 'connect'	# // 'connect'/'query'
				# // если метод auth_tp 'query'
			   	# // в Api дожен быть реализован метод
			    	# // "get_auth_query(**connect_params)"

    engine = websockets
    connect_params = None

    wsurl = None

    parting_msg = None

    adapters = {}

    @classmethod
    def pass_basequote_map(cls, basequote_map):
        cls.basequote_map.update(basequote_map)

    @classmethod
    def update_basequote_map(cls, exfrmt, base, quote):
        if not cls.basequote_map.get(exfrmt.upper()):
            cls.basequote_map[exfrmt.upper()] = (base.upper(), quote.upper())

    @classmethod
    def get_inheritors(cls):
        inheritors = []
        for inheritor in cls.__subclasses__():
            if issubclass(inheritor, Stream) or issubclass(inheritor, GetRequest):
                inheritors.append(inheritor)
        return inheritors

    @classmethod
    def init(cls):
        if cls.basequote_map is None:
            cls.basequote_map = {}
        if cls.markets_aliases is None:
            cls.markets_aliases = {}
        if cls.connect_params is None:
            cls.connect_params = {}

    def __init__(self, **connection_params):
        # is_inheritor = connection_params.get('inheritor')
        # if is_inheritor:
        #	self.__init_inheritor__(**connection_params)

	#чет какое-то дикое уродство
        self.init()
        cp = connection_params.copy()
        self.ignore_greeting = cp.pop('ignore_greeting', self.ignore_greeting)
        self.ignore_heartbeat = cp.pop('ignore_heartbeat', self.ignore_heartbeat)
        self.ignore_ping = cp.pop('ignore_ping', self.ignore_ping)
        self.ignore_pong = cp.pop('ignore_pong', self.ignore_pong)
        self.ignore_success = cp.pop('ignore_success', self.ignore_success)

        self.basequote_map.update(cp.pop('basequote_map', {}))
        self.markets_aliases.update(cp.pop('markets_aliases', {}))
        self.auth = cp.pop('auth', self.auth)
        self.engine = cp.pop('engine', self.engine)

        self.timeout_silence = cp.pop('timeout_silence', self.timeout_silence)
        self.timeout = cp.pop('timeout', self.timeout)

        self.connect_params = {**self.connect_params, **cp}

        inheritors = self.get_inheritors()
        self.adapters = {}
        for inheritor in inheritors:
            adapter = inheritor()
            self.adapters[adapter.rname] = adapter

    # def __init_inheritor__(self, **connection_params):
    #	self.rname = f'{self.rtp}_{self.dtp}'.lower()
    #	self.rkey = namedtuple(self.rname, self.order)

    async def get_ws_options(self, **connect_params):
        wsurl = await self.get_wsurl(**connect_params)
        engine = connect_params.pop('engine', self.engine)
        connect_params = {**self.connect_params, **connect_params}
        if self.autoTracking:

            connect_params['ping_interval'] = self.timeout_silence
            connect_params['ping_timeout'] = self.timeout
        else:
            connect_params['ping_interval'] = 0
            connect_params['ping_timeout'] = 0

        return {
            'engine': engine,
            'wsurl': wsurl,
            'options': connect_params
        }

    async def get_wsurl(self, **connect_params):
        return self.wsurl

    def build_query(self, *requests_params):
        if len(requests_params) > 1:
            raise NotImplementedError
        else:
            raise NotImplementedError

    def build_query_unsub(self, **rkeys):
        raise NotImplementedError

    def build_ping_query(self):
        raise NotImplementedError

    @staticmethod
    def encode(msg):
        return json.dumps(msg)

    def parse_errex(self, tm, errex, action):
        if errex.reason == 'Too many requests':
            msg = {
                'tm': tm,
                'kind': CLOSED,
                'tp': OUT_OF_LIMITS,
                'errex': errex,
            }
        else:
            msg = {
                'tm': tm,
                'kind': CLOSED,
                'tp': UNKNOWN,
                'errex': errex
            }

        return [msg]

    def parse(self, tm, msg):
        try:
            decoded = self.decode(msg)
        except Exception as errex:
            return self.on_decode_error(tm, msg, errex)
        try:
            return self.parse_msg(tm, decoded)
        except Exception as errex:
            return self.on_parsing_error(tm, decoded, errex)

    def decode(self, msg):
        return json.loads(msg)

    def on_decode_error(self, tm, msg, errex):
        return [{
            'tm': tm,
            'kind': DECODE_ERROR,
            'tp': None,
            'errex': errex,
            'msg': msg
        }]

    def on_parsing_error(self, tm, msg, errex):
        return [{
            'tm': tm,
            'kind': PARSE_ERROR,
            'tp': None,
            'errex': errex,
            'msg': msg
        }]

    def parse_msg(self, tm, msg):
        raise NotImplementedError

    def parse_greeting(self, tm, msg):
        return {
            'tm': tm,
            'kind': SERVICE,
            'tp': GREETING
        }

    def parse_pong(self, tm, msg):
        return {
            'tm': tm,
            'kind': SERVICE,
            'tp': PONG
        }

    def parse_heartbeat(self, tm, msg):
        return {
            'tm': tm,
            'kind': SERVICE,
            'tp': HEARTBEAT
        }

    def parse_service_greeting(self, tm, msg):
        return self.parse_greeting(tm, msg)

    def parse_service_pong(self, tm, msg):
        return self.parse_pong(tm, msg)

    def parse_service_heartbeat(self, tm, msg):
        return self.parse_heartbeat(tm, msg)

    def parse_close_errex(self, tm, errex):
        ...

    def symbol_to_exfrmt(self, symbol):
        base, quote = self.extract_basequote_infrmt(symbol)
        symbol = self.join_basequote_exfrmt(base, quote)
        self.update_basequote_map(symbol, base, quote)
        return symbol

    def symbol_to_infrmt(self, symbol):
        base, quote = self.extract_basequote_exfrmt(symbol)
        symbol = self.join_basequote_infrmt(base, quote)
        return symbol

    def extract_basequote_infrmt(self, symbol):
        quote, base = symbol.split('-')
        return base, quote

    def extract_basequote_exfrmt(self, symbol):
        basequote = self.basequote_map.get(symbol)
        if not basequote:
            raise UnknownMarket(symbol)
        return basequote

    def join_basequote_infrmt(self, base, quote):
        return f'{quote}-{base}'

    def join_basequote_exfrmt(self, base, quote):
        raise NotImplementedError

    def get_conflict_keys(self, request_name, *args, **kwargs):
        return self.adapters[request_name].get_conflict_keys(*args, **kwargs)

    def get_rkey(self, request_name, *args, **kwargs):
        return self.adapters[request_name].get_rkey(*args, **kwargs)


class Stream:
    rtp = SUB
    dtp = None
    order = None

    def __init__(self):
        self.rname = f'{self.rtp}_{self.dtp}'.lower()
        self.rkey = namedtuple(self.rname, [*self.order, 'request'], defaults=[self.rname])

    # def build_query(self, *args, **kwargs):
    #	request_params = (self.rname, args, kwargs)
    #	return super().build_query(request_params)

    def get_rkey(self, *args, **kwargs):
        values = [kwargs.get(param) for param in self.order[len(args):]]
        return self.rkey(*args, *values)

    def build_request(self, *args, **kwargs):
        raise NotImplementedError

    def parse(self, tm, msg):
        raise NotImplementedError

    def get_conflict_keys(self, *args, **kwargs):
        return [self.get_rkey(*args, **kwargs)]


class GetRequest(Stream):
    rtp = GET
    dtp = None


def safesend(method):
    async def wrapper(self, *args, **kwargs):
        if self.active:
            return await method(self, *args, **kwargs)
        else:
            if self.closed:
                raise RequestsForbidden('closed')
            elif not self.connected:
                raise RequestsForbidden('not_connected')
            else:
                raise Exception('?')

    return wrapper


class Connection:
    connect_params = {}

    id_next = Sequence(1).next
    lifetime = None

    def __init__(self, Api, callback=None, **connection_params):
        self.id = self.id_next()

        self.callback = None
        if callback:
            self.set_callback(callback)

        # self.lifetime=connection_params.get('lifetime') or self.lifetime

        self.api = Api(**connection_params)

        self.connected = False
        self.closed = False
        self.active = False

        self.recv_task = None

        self.ping_activity_task = asyncio.Future()
        self.ping_regular_task = asyncio.Future()
        self.close_timeout_task = asyncio.Future()
        self.ping_activity_sending = None
        self.disconnect_task = None

        self.connected_at = 0
        self.last_at = 0

        self.requests_set = set([])

        for request_name in self.api.adapters:
            self._bake_requests_interface(request_name)

        self.requests_set_prepared = set([])
        self.requests_prepared = []

        self.lock = asyncio.Lock()

    async def acquire(self):
        await self.lock.acquire()

    def locked(self):
        return self.lock.locked()

    def release(self):
        self.lock.release()

    def set_callback(self, callback):
        if iscoroutinefunction(callback):
            self.callback = callback
        else:
            self.callback = as_async(callback)

    def _bake_requests_interface(self, rname):

        async def request_interface(*args, **kwargs):

            if self.active:
                conflict_keys = self.api.get_conflict_keys(rname, *args, **kwargs)
                rkey = conflict_keys[0]

                conflicts = self._find_conflicts(conflict_keys)
                if conflicts:
                    raise RequestsConflict(conflicts)
                query = self.api.build_query((rname, args, kwargs))
                await self.send(query)
                self.requests_set.add(rkey)
                return rkey
            else:
                if self.closed:
                    raise RequestsForbidden('closed')
                elif not self.connected:
                    raise RequestsForbidden('not_connected')
                else:
                    raise Exception('?')

        setattr(self, rname, request_interface)

    async def connect(self, **connect_params):
        if not self.callback:
            raise Exception('set callback')

        if self.connected:
            raise ReconnectForbidden
            
        connect_params = {**self.connect_params, **connect_params}

        ws_options = await self.api.get_ws_options(**connect_params)

        engine = ws_options['engine']
        wsurl = ws_options['wsurl']
        options = ws_options['options']

        try:
            self.ws = await engine.connect(wsurl, **options)
        except Exception as errex:
            raise self.on_connect_failure(errex, wsurl, options)
        else:
            if self.api.auth_tp == 'query':
                await self.auth(**connect_params)
            self.connected = True
            self.active = True
            self.connected_at = time.time()

            self.run_service_tasks()

            return True

    def run_service_tasks(self):
        self.recv_task = asyncio.create_task(self.recv_forever())

        if self.api.regular_ping:
            self.ping_regular_task = asyncio.create_task(self.ping_regular_coro())

        if not self.api.autoTracking:
            self.ping_activity_task = asyncio.create_task(self.ping_activity_coro())
            self.close_timeout_task = asyncio.create_task(self.close_timeout_coro())

    async def ping_regular_coro(self):
        await asyncio.sleep(self.api.ping_regular)
        while self.active:
            await self.send_ping_regular()
            await asyncio.sleep(self.api.ping_regular)

    async def send_ping_regular(self):
        raise NotImplementedError

    async def ping_activity_coro(self):
        await asyncio.sleep(self.api.timeout_silence)
        while self.active:
            td = self.api.timeout_silence - (time.time() - self.last_at)
            if td > 0:
                if self.ping_activity_sending:
                    self.ping_activity_sending.cancel()
                    self.ping_activity_sending = None
                await asyncio.sleep(td)
            else:
                if self.ping_activity_sending:
                    await asyncio.sleep(self.api.timeout_silence)
                    continue
                self.ping_activity_sending = asyncio.create_task(self.send_ping_activity())

    async def send_ping_activity(self):
        raise NotImplementedError

    async def close_timeout_coro(self):
        await asyncio.sleep(self.api.timeout)
        while self.active:
            td = self.api.timeout - (time.time() - self.last_at)
            if td > 0:
                await asyncio.sleep(td)
            else:
                ...
                await self._disconnect()

    async def auth(self, *args, **kwargs):
        raise NotImplementedError

    def on_connect_failure(self, errex, wsurl, options):
        return NotConnected('unknown', errex, wsurl, options)

    async def disconnect(self):
        if not self.connected:
            raise WasNotConnected
        await self._disconnect()

    async def disconnect_nowait(self):
        if not self.connected:
            raise WasNotConnected
        await self._disconnect()

    def _disconnect(self):
        self.active = False
        self._cancel_services()
        if not self.disconnect_task:
            self.disconnect_task = asyncio.create_task(self._close())
        return self.disconnect_task

    def _cancel_services(self):
        self.recv_task.cancel()
        self.ping_activity_task.cancel()
        self.ping_regular_task.cancel()
        self.close_timeout_task.cancel()

    async def _close(self):
        await self.ws.close()
        self.closed = True

    async def recv_forever(self):
        if not self.api.pingpong:
            while self.active:
                msgs = await self.recv()
                for msg in msgs:

                    if msg['kind'] == RESPONSE or msg['tp'] == UNSUB:
                        self.requests_set.remove(msg['rkey'])
                    await self.callback(msg)
        else:
            while self.active:
                msgs = await self.recv()
                for msg in msgs:
                    if msg.get('pong'):
                        await self.send(msg['pong'])
                    else:
                        if msg['kind'] == RESPONSE or msg['tp'] == UNSUB:
                            self.requests_set.remove(msg['rkey'])
                        await self.callback(msg)
        await self._disconnect()

    async def recv(self):
        try:
            msg = await self.ws.recv()
            self.last_at = time.time()

        except websockets.ConnectionClosed as errex:
            #self.E = errex
            if self.active:
                self.active = False
                msgs = self.on_errex(time.time(), errex, 'recv')
            else:
                msgs = []
        else:
            msgs = self.on_msg(self.last_at, msg)
        return msgs

    def on_errex(self, tm, errex, action):
        msgs = self.api.parse_errex(tm, errex, action)
        return msgs

    def on_msg(self, tm, msg):
        msgs = self.api.parse(tm, msg)
        return msgs

    @safesend
    async def unsub(self, *rkeys):
        query = self.api.build_query_unsub(*rkeys)
        await self.send(query)

    @safesend
    async def in_one_query(self, *requests):
        rkeys = []
        requests_params = []
        conflict_keys_list = []

        for i, request_coro in enumerate(requests):
            request_name, args, kwargs = self.inspect_request_coro(request_coro)
            conflict_keys = self.api.get_conflict_keys(request_name, *args, **kwargs)

            rkey = conflict_keys[0]
            rkeys.append(rkey)
            conflict_keys_list.append(conflict_keys)
            requests_params.append((request_name, args, kwargs))

        self.check_conflicts_send_union(conflict_keys_list)
        self.check_conflicts(conflict_keys_list)

        query = self.api.build_query(*requests_params)
        await self.send(query)
        self.requests_set.update(rkeys)
        return rkeys

    def prepare_request(self, request_name, *args, **kwargs):
        conflict_keys = self.api.get_conflict_keys(request_name, *args, **kwargs)
        rkey = conflict_keys[0]

        conflicts = self._find_conflicts(conflict_keys)
        if conflicts:
            raise RequestsConflict(conflicts)

        self.requests_set_prepared.add(rkey)
        self.requests_prepared.append((request_name, args, kwargs))
        return rkey

    def cancel_prepared(self):
        self.requests_set_prepared = set([])
        self.requests_prepared = []

    @safesend
    async def send_prepared(self):
        query = self.api.build_query(*self.requests_prepared)
        self.requests_set.update(self.requests_set_prepared)
        self.requests_set_prepared = set([])
        self.requests_prepared = []
        await self.send(query)

    # return rkeys

    @staticmethod
    def inspect_request_coro(coroutine):
        params = coroutine.cr_frame.f_locals
        request_name = coroutine.cr_code.co_name
        args = params['args']
        kwargs = params['kwargs']
        return request_name, args, kwargs

    def find_conflicts(self, request_coro):
        '''
        проверяет запрос на предмет конфликта с существубщим запросом.
        '''
        request_name, args, kwargs = self.inspect_request_coro(request_coro)
        adapter = self.api.get_adapter(request_name)
        conflict_keys = adapter.get_conflict_keys(*args, **kwargs)

        return self._find_conflicts(conflict_keys)

    def _find_conflicts(self, conflict_keys):
        conflicts = set([])
        for key in conflict_keys:
            if ANY in key:
                tp = type(key)
                significant = []
                for i, value in enumerate(key):
                    if value != ANY:
                        significant.append(i)
                for rkey in self.requests_set:
                    if not isinstance(rkey, tp):
                        continue
                    for i in significant:
                        if rkey[i] != key[i]:
                            break
                    else:
                        conflicts.add(rkey)
                for rkey in self.requests_set_prepared:

                    if not isinstance(rkey, tp):
                        continue
                    for i in significant:
                        if rkey[i] != key[i]:
                            break
                    else:
                        conflicts.add(rkey)

            else:
                if key in self.requests_set:
                    conflicts.add(key)
                if key in self.requests_set_prepared:
                    conflicts.add(key)

        return conflicts

    def check_conflicts_send_union(self, conflict_keys_list):
        reqmap_local = {}
        for req_id, conflict_keys in enumerate(conflict_keys_list):
            rkey = conflict_keys[0]

            if not reqmap_local.get(rkey):
                reqmap_local[rkey] = []
            reqmap_local[rkey].append(req_id)

            for conflict_key in conflict_keys[1:]:
                if ANY in conflict_key:
                    tp = type(conflict_key)
                    significant = []
                    for i, value in enumerate(conflict_key):
                        if value != ANY:
                            significant.append(i)
                    for any_key in reqmap_local:
                        if not isinstance(any_key, tp):
                            continue
                        for i in significant:
                            if any_key[i] != conflict_key[i]:
                                break
                        else:
                            reqmap_local[rkey].extend(reqmap_local[any_key])
                            reqmap_local[any_key].append(req_id)
                else:
                    reqmap_local[rkey].extend(reqmap_local.get(conflict_key, []))
                    if reqmap_local.get(conflict_key):
                        reqmap_local[conflict_key].append(req_id)

        conflicts = []

        for request_key, req_ids in reqmap_local.items():
            if len(req_ids) > 1:
                conflicts.append(req_ids)
        if conflicts:
       
            raise RequestsConflicts_union(conflicts)

    def check_conflicts(self, conflict_keys_list):
        conflicts_all = {}
        for req_id, conflict_keys in enumerate(conflict_keys_list):
            conflicts = set([])
            for conflict_key in conflict_keys:
                if ANY in conflicts:
                    tp = type(conflict_key)
                    significant = []
                    for i, value in enumerate(conflict_key):
                        if value != ANY:
                            significant.append(i)
                    for any_key in self.requests_set:
                        if not isinstance(any_key, tp):
                            continue

                        for i in significant:
                            if any_key[i] != conflict_key[i]:
                                break
                        else:
                            conflicts.add(any_key)
                else:
                    if conflict_key in self.requests_set:
                        conflicts.add(conflict_key)
            if conflicts:
                conflicts_all[req_id] = conflicts
        if conflicts_all:
            raise RequestsConflict(conflicts_all)

    async def send(self, query):

        try:
            await self.ws.send(query)
        except Exception as errex:
            self.E = errex
            if self.active:
                self.active = False
                msgs = self.on_errex(time.time(), errex, 'send')
                for msg in msgs:
                    await self.callback(msg)
            await self._disconnect()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
