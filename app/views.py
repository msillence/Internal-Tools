from flask import render_template, request, Response, session, url_for, flash, redirect
from flask.ext.wtf import Form
from numbers import Number
from datetime import datetime
from wtforms import TextField, PasswordField, validators
from urllib import parse
import pyodbc, json, requests, datetime, time
import xml.etree.ElementTree as ET
from app import app

# Framework
class LoginForm(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

def logged_in():

	if 'username' not in session or 'password' not in session:
		return False
		
	try:
		execute_query('SELECT * FROM sysibm.sysdummy1')
	except pyodbc.Error as err:
		return False
		
	return True			
	
def execute_query(sql, parms = []):

	connection_string = 'DSN=TRACEY;UID=' + session['username'] + ';PWD=' + session['password'] + ';CHARSET=UTF8;'
	connection        = pyodbc.connect(connection_string, autocommit=True)
	cursor            = connection.cursor()	
	return cursor.execute(sql, parms)

# FST Job List
class Job:

	def __init__(self, number, client, shortText,  longText, assignedTo, status, priority, functionalArea):
		self.number = number
		self.client = client
		self.shortText = shortText
		self.longText = longText
		self.assignedTo = assignedTo
		self.status = status
		self.priority = priority
		self.functionalArea = functionalArea

class Area:

	def __init__(self, functionalArea, numberOfJobs = 0):
		self.functionalArea = functionalArea
		self.numberOfJobs = numberOfJobs

class Priority:

	def __init__(self, level, numberOfJobs):
		self.level = level
		self.numberOfJobs = numberOfJobs

class Client:

	def __init__(self, name, numberOfJobs = 0):
		self.name = name
		self.numberOfJobs = numberOfJobs

class Status:

	def __init__(self, name, numberOfJobs = 0):
		self.name = name
		self.numberOfJobs = numberOfJobs		
		
class JobHistory:

	def __init__(self, date, numberOfJobs = 0):
		self.year = str(date)[0:4]
		self.month = str(int(str(date)[4:6]) - 1)
		self.day = str(date)[6:8]
		self.numberOfJobs = numberOfJobs			
		
class FilterOptions:

	def __init__(self, priority, client, assignedTo, jobText, functionalArea, status):

		self.priority = priority
		self.client = client
		self.assignedTo = assignedTo
		self.jobText = jobText
		self.functionalArea = functionalArea
		self.status = status
	
# File Browser
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

		# Return everything as JSON with a custom encoder to deal with dates/numbers
		return json.dumps(output, cls = MyEncoder)	
				
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

#############################################
# Common Routes
#############################################			
@app.route('/login', methods=['GET', 'POST'])
def login():

	form = LoginForm()
	
	if form.validate_on_submit():

		session['username'] = form.username.data.upper()
		session['password'] = form.password.data
		
		if logged_in():		
			return redirect(url_for('overview'))		
		else:
			flash('Invalid username or password')
		
	return render_template("login.html", form=form)
	
#############################################
# FST Job List Helper Methods
#############################################	
def getPriorityData():
		
	sql = '''SELECT CAST(jobs3.import AS CHAR(1)) AS "Priority", count(*)
			FROM jobs3                                                               
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			GROUP BY CAST(jobs3.import AS CHAR(1))
			ORDER BY CAST(jobs3.import AS CHAR(1))'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	priorityList = []
	
	for row in data:
		priority = Priority(row[0], row[1])
		priorityList.append(priority)

	return priorityList
	
def build_xml_tree():

	root = ET.Element("PriorityCount")
	
	for priority in getPriorityData():
		priorityNode = ET.SubElement(root, "Priority")
		priorityNode.set('value', str(priority.level))
		priorityNode.set('count', str(priority.numberOfJobs))
		
	xml_string = ET.tostring(root)
	return xml_string	
	
#############################################
# FST Job List Routing
#############################################
@app.route("/jobs/joblist", methods = ["GET"])
def job_list():

	if not logged_in():
		return redirect(url_for('login'))	

	queryString = parse.unquote(request.query_string.decode("utf-8"))
	parameters = {}

	for parameter in queryString.split('&'):
		if "=" in parameter:
			parameters[parameter.split('=')[0]] = parameter.split('=')[1]

	priority = parameters.get('priority','')
	client = parameters.get('client','')
	assignedTo = parameters.get('assignedto','')
	jobText = parameters.get('jobtext','')
	functionalArea = parameters.get('functionalarea','')
	status = parameters.get('status','')

	filterOptions = FilterOptions(priority, client, assignedTo, jobText, functionalArea, status)

	sql = '''SELECT  jobs3.codex AS "Job Number", 
				CAST(jobs3.client AS CHAR(5) CCSID 1208) AS "Client", 
				CAST(jobs3.descrq AS CHAR(160) CCSID 1208) AS "Description",
				CAST(jobs3.descrp AS CHAR(160) CCSID 1208),
				CAST(IFNULL(tearner.tename, 'Queue') AS CHAR(20) CCSID 1208) || '(' || CAST(IFNULL(tearner.teear, 'N/A') AS CHAR(4) CCSID 1208) || ')' AS "Assignee",
				CAST(jobs3.status AS CHAR(1) CCSID 1208) AS "Status", 
				CAST(jobs3.import AS CHAR(1) CCSID 1208) AS "Priority", 
				CAST(SUBSTR(jobs3.extra1,1,3) AS CHAR(3) CCSID 1208) || '-' || CAST(SUBSTR(jobs3.extra1,4,3) AS CHAR(3) CCSID 1208) AS "Functional Area"			
			FROM jobs3 LEFT OUTER JOIN tearner ON jobs3.whodo=tearner.teear                                                                
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			ORDER BY CAST(jobs3.import AS CHAR(1)), jobs3.codex '''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	jobList = []

	for row in data:
		job = Job(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
		jobList.append(job)

	sql = '''SELECT DISTINCT CAST(jobs3.client AS CHAR(5) CCSID 1208) AS "Client"
			FROM jobs3                                                              
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			ORDER BY CAST(jobs3.client AS CHAR(5) CCSID 1208)'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()			
		
	clientList = []

	for row in data:
		client = Client(row[0].strip())
		clientList.append(client)	

	sql = '''SELECT DISTINCT CAST(SUBSTR(jobs3.extra1,1,3) AS CHAR(3)) || '-' ||  CAST(SUBSTR(jobs3.extra1,4,3) AS CHAR(3)) AS "Functional Area"
			FROM jobs3                                                           
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			ORDER BY CAST(SUBSTR(jobs3.extra1,1,3) AS CHAR(3)) || '-' ||  CAST(SUBSTR(jobs3.extra1,4,3) AS CHAR(3))'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	functionalAreaList = []

	for row in data:
		functionalArea = Area(row[0])
		functionalAreaList.append(functionalArea)	
	
	sql = '''SELECT DISTINCT CAST(jobs3.status AS CHAR(1)) AS "Status"
			FROM jobs3                                                           
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			ORDER BY CAST(jobs3.status AS CHAR(1))'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	statusList = []

	for row in data:
		status = Status(row[0])
		statusList.append(status)	
	
	return render_template("jobs-list.html", jobList = jobList, clientList = clientList, functionalAreaList = functionalAreaList, statusList = statusList, filterOptions = filterOptions)

@app.route("/jobs/overview", methods = ["GET"])
def overview():

	if not logged_in():
		return redirect(url_for('login'))	

	sql = '''SELECT CAST(SUBSTR(jobs3.extra1,1,3) AS CHAR(3)) || '-' ||  CAST(SUBSTR(jobs3.extra1,4,3) AS CHAR(3)) AS "Functional Area", count(*)
			FROM jobs3                                                               
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			GROUP BY CAST(SUBSTR(jobs3.extra1,1,3) AS CHAR(3)) || '-' ||  CAST(SUBSTR(jobs3.extra1,4,3) AS CHAR(3))
			ORDER BY CAST(SUBSTR(jobs3.extra1,1,3) AS CHAR(3)) || '-' ||  CAST(SUBSTR(jobs3.extra1,4,3) AS CHAR(3))'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	areaList = []
	
	for row in data:
		area = Area(row[0], row[1])
		areaList.append(area)		

	sql = '''SELECT CAST(jobs3.client AS CHAR(5)) AS "Client", count(*)
			FROM jobs3                                                               
			WHERE jobs3.jtype='J' 
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN') 
				AND jobs3.client NOT IN ('RTREG','JHC') 
				AND jobs3.chnnel IN ('FST','FST3') 
				AND jobs3.status NOT IN ('F','C', 'S', 'I') 
			GROUP BY CAST(jobs3.client AS CHAR(5))
			ORDER BY CAST(jobs3.client AS CHAR(5))'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	clientList = []
	
	for row in data:
		client = Client(row[0], row[1])
		clientList.append(client)						

	sql = '''SELECT CAST(jobs3.status AS CHAR(1)) AS "Status", count(*) 
			FROM jobs3                                              
			WHERE jobs3.jtype='J'                                   
				AND jobs3.system IN ('FIGHD','HELPD','FIGLW','KNOWN')  
				AND jobs3.client NOT IN ('RTREG','JHC')                
				AND jobs3.chnnel IN ('FST','FST3')                     
				AND jobs3.status NOT IN ('F','C', 'S', 'I')            
			GROUP BY CAST(jobs3.status AS CHAR(1))                  
			ORDER BY CAST(jobs3.status AS CHAR(1))'''
	
	curs = execute_query(sql)		
	data = curs.fetchall()	
	
	statusList = []
	
	for row in data:
		status = Status(row[0], row[1])
		statusList.append(status)					
	
	total = 0
	priorityList = getPriorityData()
	
	for priority in priorityList:
		total = total + priority.numberOfJobs
		
	sql = '''SELECT sum(jobs_opened), sum(jobs_closed) 
			  FROM wapr.job_stats                     
			 WHERE date > ''' + str(int(time.strftime('%Y%m')) * 100)

	curs = execute_query(sql)		
	data = curs.fetchall()			
	monthlyJobsOpened = data[0][0]
	monthlyJobsClosed = data[0][1]
	monthlyAverageResolution = 0

	if time.strftime('%m') in ['01', '02', '03']:
		quarterDate = 100
	elif time.strftime('%m') in ['04', '05', '06']:
		quarterDate = 400
	elif time.strftime('%m') in ['07', '08', '09']:
		quarterDate = 700	
	else:
		quarterDate = 1000
		
	sql = '''SELECT sum(jobs_opened), sum(jobs_closed) 
			  FROM wapr.job_stats                     
			 WHERE date > ''' + str(int(time.strftime('%Y')) * 10000 + quarterDate)
	
	curs = execute_query(sql)		
	data = curs.fetchall()			
	quarterlyJobsOpened = data[0][0]
	quarterlyJobsClosed = data[0][1]
	quarterlyAverageResolution = 0
	
		
	return render_template("jobs-overview.html", areaList = areaList, priorityList = getPriorityData(), clientList=clientList, statusList=statusList, total=total, monthlyJobsOpened=monthlyJobsOpened, monthlyJobsClosed=monthlyJobsClosed, monthlyAverageResolution=monthlyAverageResolution, quarterlyJobsOpened=quarterlyJobsOpened, quarterlyJobsClosed=quarterlyJobsClosed, quarterlyAverageResolution=quarterlyAverageResolution)

@app.route("/jobs/history", methods = ["GET"])
def history():	

	if not logged_in():
		return redirect(url_for('login'))	
		
	return render_template("jobs-history.html")

@app.route("/jobs/history_chart", methods = ["GET"])
def history_chart():	

	sql = '''select                                 
			a.date,                          
			a.net_change                     
			+ COALESCE((select sum(net_change)
			from wapr.job_stats AS b       
			where b.date <= a.date),0)      
			from wapr.job_stats AS a         
			ORDER BY a.date '''                          

	curs = execute_query(sql)		
	data = curs.fetchall()	

	jobHistory = {}
	jobHistory['cols'] = [{'id': 'date', 'label': 'date', 'type':'date'}, {'id':'openJobs', 'label':'Open Jobs', 'type': 'number'}]
	jobHistory['rows'] = []
		
	for row in data:
		newRow = ({'c':[]})
		dt = datetime.datetime.strptime(str(row[0]),'%Y%m%d')	
		newRow['c'].append({'v': dt.strftime('%Y-%m-%d')})
		newRow['c'].append({'v': row[1]})
		jobHistory['rows'].append(newRow)	
		
	return json.dumps(jobHistory, cls = MyEncoder)		
	
@app.route("/jobs/job", methods = ["GET"])	
@app.route("/jobs/job/<job>", methods = ["GET"])
def job_detail(job = 0):	

	sql = '''SELECT CAST(text79 AS CHAR(79) CCSID 1208)                
				FROM jhcjutil.jobscrat         
			WHERE codex = ?    
			ORDER BY pagnum, linnum '''         

	curs = execute_query(sql, parms = [job])		
	data = curs.fetchall()				
			
	text = '<pre>'
	
	for row in data:
		text = text + row[0] + '<br>' 

	text = text + '</pre>'
		
	return text
	
@app.route("/jobs/priorityxml", methods = ["GET"])	
def stats_by_priority_xml():	

	xml_string = build_xml_tree()
	return Response(xml_string, mimetype='text/xml')		

#############################################
# File Browser Routing
#############################################
@app.route('/files/<library>/<table>/')
def view(library, table):

	if not logged_in():
		return redirect(url_for('login'))	

	tableInstance = Table(library, table)
	
	return render_template("files-main.html", columns = tableInstance.columns, library = library, table = table)		
	
@app.route('/files/<library>/<table>/data')
def get_data(library, table):		
		
	if not logged_in():
		return redirect(url_for('login'))		
		 	
	sEcho           = request.args.get('sEcho')		
	firstRecord     = int(request.args.get('iDisplayStart')) + 1
	pageSize        = int(request.args.get('iDisplayLength'))
	sortColumn      = int(request.args.get('iSortCol_0')) + 1
	sortDirection   = request.args.get('sSortDir_0')
	numberOfColumns = int(request.args.get('iColumns'))
	
	searchColumns = {}
	for i in range (0,numberOfColumns):
		if request.args.get('sSearch_' + str(i)) != '':
			searchColumns[i] = request.args.get('sSearch_' + str(i))
			
	table = Table(library, table)
	
	return table.data(firstRecord, pageSize, searchColumns, sortColumn, sortDirection, numberOfColumns, sEcho)	
	