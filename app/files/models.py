import json

from app.views import execute_query
from app.models import MyEncoder

class Table():

	def __init__(self, library, table):
		self.library = library.upper()
		self.table = table.upper()
		
		curs = execute_query('SELECT * FROM (SELECT row_number() over () as rownum, rrn(a) AS rrn, a.* FROM ' + library.upper() + '.' + table.upper() + ' AS a) AS b ')	
		self.columns = [column[0] for column in curs.description]
		
	def data(self, firstRecord, pageSize, searchColumns, sortColumn, sortDirection, numberOfColumns, sEcho):
	
		# Unfiltered Record Count
		curs = execute_query('SELECT count(*) FROM ' + self.library + '.' + self.table)
		unfilteredRecordCount = curs.fetchone()[0]
		
		# Start building the SQL query
		sql = ' FROM (SELECT row_number() over () as rownum, rrn(a) AS rrn, a.* FROM '
		sql = sql + self.library + '.' + self.table + ' AS a WHERE 1=1'

		for key, value in searchColumns.items():
			sql = sql + ' AND UPPER(CAST(' + self.columns[key] + " AS char(5000))) LIKE ('%" + value.upper() + "%') "		
		
		# Filtered Record Count
		curs = execute_query('Select count(*) ' + sql + ') AS b')
		filteredRecordCount = curs.fetchone()[0]
		
		# Restrict to just a single page of data at a time
		sql = sql + ') AS b WHERE b.rownum BETWEEN ' + str(firstRecord) + ' AND ' + str(firstRecord + pageSize - 1)
		
		if sortColumn:
			sql = sql + ' ORDER BY ' + str(sortColumn) 
			sql = sql + ' ' + sortDirection	
		
		sql = sql + ' OPTIMIZE FOR ' + str(pageSize) + ' ROWS'	
			
		curs = execute_query('Select * ' + sql)
		data = curs.fetchall()	
	
		# Build the dictionary that we'll eventually collapse into JSON
		output = {}
		output['sEcho'] = sEcho
		output['iTotalRecords'] = str(unfilteredRecordCount)
		output['iTotalDisplayRecords'] = str(filteredRecordCount)	
		
		output['aaData'] = []
		
		for row in data:	
			for idx, value in enumerate(row):
				if value is None:
					row[idx] = 'Null'
			output['aaData'].append(list(row))

		return json.dumps(output, cls = MyEncoder)
