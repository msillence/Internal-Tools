
from app.views import execute_query

def getAllRevenueEntries():

	sql = '''SELECT r.id, r.client_id, c.name, p.desc, r.project_code, r.year, r.month, r.value
	           FROM wapr.revenue AS r
			     INNER JOIN wapr.jhc_client AS c ON r.client_id = c.id
				 LEFT OUTER JOIN project AS p ON r.project_code = p.procde
			 ORDER BY c.name, r.project_code'''
	
	curs = execute_query(sql)	

	return curs.fetchall()

def getSummaryByMonth():

	sql = '''SELECT r.client_id, c.name, r.year, r.month,             
				   sum(r.value) AS total_value                       
			  FROM wapr.revenue AS r                                 
				INNER JOIN wapr.jhc_client AS c ON r.client_id = c.id
			GROUP BY r.client_id, c.name, r.year, r.month            
			ORDER BY c.name'''
	
	curs = execute_query(sql)	

	return curs.fetchall()		
	
def getSummaryByYear():

	sql = '''SELECT r.client_id, c.name, r.year, sum(r.value) AS total_value                       
			  FROM wapr.revenue AS r                                 
				INNER JOIN wapr.jhc_client AS c ON r.client_id = c.id
			GROUP BY r.client_id, c.name, r.year           
			ORDER BY c.name'''
	
	curs = execute_query(sql)	

	return curs.fetchall()	
	
def createRevenueEntry(client, project, year, month, value):

	sql = '''INSERT INTO wapr.revenue (client_id, project_code, year, month, value)
				VALUES(?, ?, ?, ?, ?)'''
				
	curs = execute_query(sql, parms=[client, project, year, month, value])				
