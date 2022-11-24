#py

from amdi.limits import Limits_simple

class Limits(Limits_simple):
	def __init__(epoch=1, msgs_per_epoch=4, reqs_per_msg=200, freespace=1000,
			connect_epoch=0.1, connect_per_epoch=1, connect_max=20):
		super().__init__(epoch, msgs_per_epoch, reqs_per_msg, freespace,
			connect_epoch, connect_per_epoch, connect_max)


