# py

class HighConnError(Exception):
    pass


class ReconnectForbidden(HighConnError):
    pass


class AlreadyClosed(HighConnError):
    pass


class WasNotConnected(HighConnError):
    pass


class RequestsForbidden(HighConnError):
    def __init__(self, reason):
        self.reason = reason


class NotConnected(HighConnError):
    def __init__(self, reason, errex, wsurl, connect_params):
        self.reason = reason
        self.errex = errex
        self.wsurl = wsurl
        self.connect_params = connect_params


class RequestsConflict(HighConnError):
    '''
    конфликт запроса с существубщим запросом
    conflict - rkey конфликтного запроса
    '''

    #conflicts = None

    def __init__(self, conflict):
        self.conflict = conflict  #:rkey //


class RequestsConflicts(RequestsConflict):
    '''
    среди запросов отправляющихся вместе
    есть конфликты с существубщими запросами
    conflict - dict
    где ключ - порядкойвый номер отправлябщегося запроса
    а занчение - rkey существущего запроса

    '''

    def __init__(self, conflicts):
        self.conflicts = conflicts  #:rkey //


class RequestsConflicts_union(RequestsConflict):
    def __init__(self, conflicts):
        self.conflicts = conflicts


class ApiError(Exception):
    pass


class InvalidParameterSet(ApiError):
    pass


class QueryBuildingError(ApiError):
    pass


class RequestsTypesConflict(QueryBuildingError):
    def __init__(self, rtp1, rtp2):
        self.rtp1 = rtp1
        self.rtp2 = rtp2


class DataTypesConflict(QueryBuildingError):
    def __init__(self, dtp1, dtp2):
        self.dtp1 = dtp1
        self.dtp2 = dtp2


class ParamsConflict(QueryBuildingError):
    """
    напрмиер  если на обменике есть каналы
    канал
    trades_agg и trades
    и можно отправить сразу несколько запросов на trades_agg или trades
    но и туда и туда в 1 запросе нельзя
    и передано 2 запроса для отправки
    в 1 agg=True в 2 agg=False
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class UnionQueryForbiden(QueryBuildingError):
    pass


class UnknownMarket(ApiError):
    def __init__(self, symbol):
        self.symbol = symbol


class UnexpectedMessage(Exception):
    pass

# class UnknownSymbols(ApiError):
#    '''
#    следует проапдейтить basequote_map
#    '''
#    def __init__(self, symbols):
#        self.symbols=symbols
