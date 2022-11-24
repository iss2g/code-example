# py
from abc import ABC, abstractmethod
import time


def get_checkpoint(uptd):
    t = time.time()
    if uptd:
        return t - t % uptd
    return t


class Limits_abc(ABC):

    @abstractmethod
    def new_session(self, connid):
        ...

    @abstractmethod
    def allowed(self, connid, request, session=None):
        ...

    @abstractmethod
    def acquire(self, connid, request, session=None):
        ...

    @abstractmethod
    def release(self, connid, session=None):
        ...

    @abstractmethod
    def rollback(self, connid, request):
        ...

    @abstractmethod
    def get_ttu(self, connid):
        ...

    @abstractmethod
    def get_workload(self, connid):
        ...

    @abstractmethod
    def allowed_unsub(self, connid, request, session=None):
        ...

    @abstractmethod
    def acquire_unsub(self, connid, request, session=None):
        ...

    @abstractmethod
    def release_unsub(self, connid, session=None):
        ...

    @abstractmethod
    def get_ttu_unsub(self, connid):
        ...

    @abstractmethod
    def allowed_connect(self):
        ...

    @abstractmethod
    def acquire_connect(self):
        ...

    @abstractmethod
    def get_ttu_connect(self):
        ...

    @abstractmethod
    def on_connect_success(self, connid):
        ...

    @abstractmethod
    def on_connect_failure(self):
        ...

    @abstractmethod
    def on_disconnect(self, connid):
        ...


class Limits_connect_simple:
    def __init__(self, epoch, per_epoch, maximum):
        self.epoch = 0.1
        self.per_epoch = per_epoch
        self.maximum = 20

        self.count = 0

        self.used = 0
        self.in_use = 0
        self.checkpoint = get_checkpoint(self.epoch)

    def update(self):
        checkpoint = get_checkpoint(self.epoch)
        if checkpoint > self.checkpoint:
            self.checkpoint = checkpoint
            self.used = 0

    def allowed(self):
        if self.count >= self.maximum:
            return False
        return self.used + self.in_use < self.per_epoch

    def get_ttu(self):	#time to up
        if self.count >= self.maximum:
            return None
        return max(0, self.checkpoint + self.epoch - time.time())

    def acquire(self):
        self.update()
        self.in_use += 1
        self.count += 1

    def on_success(self):
        self.update()
        self.in_use -= 1
        self.used += 1

    def on_failure(self):
        self.on_success()
        self.count -= 1

    def on_close(self):
        self.count -= 1


class Limits_connection_simple:
    def __init__(self, epoch, msgs_per_epoch, reqs_per_msg, freespace):
        self.epoch = epoch
        self.msgs_per_epoch = msgs_per_epoch
        self.reqs_per_msg = reqs_per_msg
        self.freespace = freespace

        self.checkpoint = get_checkpoint(self.epoch)

        self.used = 0
        self.in_use = 0

        self.sid = 0
        self.reqs = {
            None: 0
        }

    def new_session(self):
        self.sid += 1
        self.reqs[self.sid] = 0  # в данном случае здесь просто будет считаться сколько запросов уже запланировано
        # для отправки в 1 сообщении
        return self.sid

    def update(self):
        checkpoint = get_checkpoint(self.epoch)
        self.checkpoint, self.used = max((checkpoint, 0), (self.checkpoint, self.used))

    def allowed(self, request, session=None):
        self.update()
        if not self.freespace:
            return False

        if self.reqs[session]:
            return self.reqs[session] < self.reqs_per_msg

        return self.used + self.in_use < self.msgs_per_epoch()

    def acquire(self, request, session=None):
        if self.reqs[session]:
            self.reqs[session] += 1
            return
        self.in_use += 1
        self.reqs[session] += 1
        self.freespace -= 1

    def release(self, session=None):
        self.update()
        self.in_use -= 1
        self.used += 1
        if session:
            self.reqs.pop(session)
        else:
            self.reqs[session] = 0

    def rollback(self, request):
        self.freespace += 1

    def get_ttu(self):
        if not self.freespace:
            return None
        return self.checkpoint + self.epoch - time.time()

    def allowed_unsub(self, request, session=None):
        self.update()
        if self.reqs[session]:
            return self.reqs[session] < self.reqs_per_msg
        return self.used + self.in_use < self.msgs_per_epoch()

    def acquire_unsub(self, request, session=None):
        if not self.reqs[session]:
            self.in_use += 1
        self.reqs[session] += 1

    def release_unsub(self, session=None):
        self.release(session)

    def get_ttu_unsub(self):
        return self.checkpoint + self.epoch - time.time()


class Limits_simple(Limits_abc):
    def __init__(self, epoch, msgs_per_epoch, reqs_per_msg, freespace,
                 connect_epoch, connect_per_epoch, connect_max):
        self.epoch = epoch
        self.msgs_per_epoch = msgs_per_epoch
        self.reqs_per_msg = reqs_per_msg
        self.freespace = freespace

        self.limits = {}
        self.limits_connect = Limits_connect_simple(connect_epoch, connect_per_epoch, 
        									connect_max)

    def allowed_connect(self):
        return self.limits_connect.allowed()

    def get_ttu_connect(self):
        return self.limits_connect.get_ttu()

    def acquire_connect(self):
        self.limits_connect.acquire()

    def on_connect_success(self, connid):
        self.limits_connect.on_success()
        self.limits[connid] = Limits_connection_simple(self.epoch, self.msgs_per_epoch,
                                                       self.reqs_per_msg, self.freespace)

    def on_connect_failure(self):
        self.limits_connect.on_failure()

    def on_disconnect(self, connid):
        self.limits.pop(connid)
        self.limits_connect.on_close()

    def new_session(self, connid):
        return self.limits[connid].new_session()

    def allowed(self, connid, request, session=None):
        return self.limits[connid].allowed(request, session)

    def acquire(self, connid, request, session=None):
        return self.limits[connid].acquire(request, session)

    def release(self, connid, session=None):
        return self.limits[connid].release(session)

    def rollback(self, connid, request):
        return self.limits[connid].rollback(request)

    def get_ttu(self, connid):
        return self.limits[connid].get_ttu()

    def allowed_unsub(self, connid, request, session=None):
        return self.limits[connid].allowed_unsub(request, session)

    def acquire_unsub(self, connid, request, session=None):
        return self.limits[connid].acquire_unsub(request, session)

    def release_unsub(self, connid, session=None):
        return self.limits[connid].release_unsub(session)

    def get_ttu_unsub(self, connid):
        return self.limits[connid].get_ttu_unsub()

# for binance:
# from amdi.ws.limits import Limits_simple
# limits=Limits_simple(epoch=1, msgs_per_epoch=4, reqs_per_msg=200, freespace=1000,
#		connect_epoch=0.1, connect_per_epoch=1, connect_max=20)
