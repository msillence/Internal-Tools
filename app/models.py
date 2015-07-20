import json, datetime
from numbers import Number

class MyEncoder(json.JSONEncoder):

	def default(self, obj):
		
		if isinstance(obj, datetime.datetime):
			return "%02d-%02d-%02d-%02d.%02d.%02d.%06d" % (obj.year,obj.month,obj.day,obj.hour,obj.minute, obj.second, obj.microsecond)
		if isinstance(obj, datetime.date):
			return "%02d-%02d-%02d" % (obj.year,obj.month,obj.day)
		if isinstance(obj, datetime.time):
			return "%02d.%02d.%02d" % (obj.hour,obj.minute, obj.second)		
		elif isinstance(obj, Number):
			return str(obj)
			
		return json.JSONEncoder.default(self, obj)	