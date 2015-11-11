from flask import Blueprint
import pyodbc, os, json

mod = Blueprint('base', __name__)		
	
def execute_query(sql, parms = []):

	with open(os.path.join(os.path.dirname(__file__), 'credentials/credentials.json')) as data_file:    
		credentials = json.load(data_file)

	connection_string = 'DSN=TRACEY;UID=' + credentials['username'] + ';PWD=' + credentials['password'] + ';CHARSET=UTF8;'
	connection        = pyodbc.connect(connection_string, autocommit=True)
	pyodbc.lowercase  = True
	cursor            = connection.cursor()
	return cursor.execute(sql, parms)
	