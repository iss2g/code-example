#py
from .api import Api
from amdi.ws import Connection

class Connection(Connection):
	def __init__(self, callback=None, Api=Api, **params):
		super().__init__(Api, callback, **params)





	

