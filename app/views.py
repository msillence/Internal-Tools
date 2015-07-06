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

class Title:
	
	def __init__ (self, main, subTitle):
		self.main = main
		self.full = main + ' - ' + subTitle
	
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
		
	def __eq__(self, other):
		return self.name == other.name

class ProjectManager:

	def __init__(self, name):
		self.name = name		

	def __eq__(self, other):
		return self.name == other.name
		
class Status:

	def __init__(self, name, numberOfJobs = 0):
		if name == 'A':
			self.name = 'Awaiting Assignment'
		elif name == 'B':
			self.name = 'Assigned'
		elif name == 'C':
			self.name = 'Closed'
		elif name == 'E':
			self.name = 'Fixed in Client Environment'
		elif name == 'H':
			self.name = 'On Hold'
		elif name == 'K':
			self.name = 'Requires Code Fix'
		elif name == 'T':
			self.name = 'In Test'
		elif name == 'W':
			self.name = 'Waiting'
		else:
			self.name = name
		
		self.numberOfJobs = numberOfJobs	
		self.letter = name
		
class FilterOptionsJobs:

	def __init__(self, priority, client, assignedTo, jobText, functionalArea, status):

		self.priority = priority
		self.client = client
		self.assignedTo = assignedTo
		self.jobText = jobText
		self.functionalArea = functionalArea
		self.status = status

class FilterOptionsProjects:

	def __init__(self, client, projectManager, status):

		self.client = client
		self.projectManager = projectManager
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

# Projects
class Project():		

	def __init__(self, row):
		self.projectCode = row[0].strip()
		self.description = row[1]
		self.client = row[2]
		self.riskLevel = row[3]
		self.owner = row[4]
		self.projectManager = row[5]
		self.designer = row[6]
		self.deliveryManager = row[7]
		self.teamLeader = row[8]
		self.testLeader = row[9]
		self.productLeader = row[10]
		self.businessAnalyst = row[11]
		self.phase = row[12]
		self.notes = '<br>'.join(row[13][i:i+64] for i in range(0, len(row[13].strip()), 64))

class Milestone():		

	def __init__(self, row):
		self.description = row[0]
		self.baseline = row[1]
		self.current = row[2]
		self.riskLevel = row[3]

class SoftwarePackage():

	def __init__(self, row):
		self.number = row[0]
		self.application = row[1]
		self.status = row[2]
		self.release = row[3]	

class Budget():

	def __init__(self, row):
		self.type = row[0]
		self.original = u"\xA3{:,.0f}".format(row[1])
		self.revised = u"\xA3{:,.0f}".format(row[2])
		self.actual = u"\xA3{:,.0f}".format(row[3])	
		self.forecast = u"\xA3{:,.0f}".format(row[4])
	
class Effort():

	def __init__(self, row):
		self.type = row[0]
		self.original = row[1]
		self.revised = row[2]
		self.actual = row[3]	
		self.forecast = row[4]
		
class Release():		

	def __init__(self, releaseNumber, projectCount):		
		self.releaseNumber = releaseNumber
		self.projectCount = projectCount
		
#############################################
# Common Routes
#############################################			
@app.route('/login', methods=['GET', 'POST'])
def login():

	url = request.args.get('url')
	
	form = LoginForm()
	
	if form.validate_on_submit():
	
		session['username'] = form.username.data.upper()
		session['password'] = form.password.data
		
		if logged_in() and url:	
			session.permanent = True
			return redirect(url)
		elif logged_in():
			session.permanent = True
			return redirect(url_for('overview'))		
		else:
			flash('Invalid username or password')
		
	return render_template("login.html", form=form, url=url)
	
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
		return redirect(url_for('login', url = url_for('job_list')))	

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

	filterOptions = FilterOptionsJobs(priority, client, assignedTo, jobText, functionalArea, status)

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
	
	return render_template("jobs-list.html", jobList = jobList, clientList = clientList, functionalAreaList = functionalAreaList, statusList = statusList, filterOptions = filterOptions, title=Title('FST Jobs', 'Jobs List'))

@app.route("/jobs/overview", methods = ["GET"])
def overview():

	if not logged_in():
		return redirect(url_for('login', url = url_for('overview')))	

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
	
		
	return render_template("jobs-overview.html", areaList = areaList, priorityList = getPriorityData(), clientList=clientList, statusList=statusList, total=total, monthlyJobsOpened=monthlyJobsOpened, monthlyJobsClosed=monthlyJobsClosed, monthlyAverageResolution=monthlyAverageResolution, quarterlyJobsOpened=quarterlyJobsOpened, quarterlyJobsClosed=quarterlyJobsClosed, quarterlyAverageResolution=quarterlyAverageResolution, title=Title('FST Jobs', 'Overview'))

@app.route("/jobs/history", methods = ["GET"])
def history():	

	if not logged_in():
		return redirect(url_for('login', url = url_for('history')))	
		
	return render_template("jobs-history.html", title=Title('FST Jobs', 'History'))

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
		return redirect(url_for('login', url = url_for('view', library=library, table=table)))	

	tableInstance = Table(library, table)
	
	return render_template("files-main.html", columns = tableInstance.columns, library = library, table = table, title= library.upper() + '/' + table.upper())		
	
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

#############################################
# Releases
#############################################	
@app.route('/releases')
def releases():

	if not logged_in():
		return redirect(url_for('login', url = url_for('releases')))

	sql = '''SELECT a.release_number, count(r.release_number)
			FROM jhcjutil.release_number_description AS a
				LEFT OUTER JOIN (SELECT r.release_number, r.project_code FROM jhcjutil.project AS p1                                       
								INNER JOIN jhcjutil.release_submissions_detail AS r             
										ON p1.procde = r.project_code						
							WHERE p1.status = 'ACTIVE'                                                            
							  AND r.release_committee_decision = 'APPROVED'
							  AND p1.closed <> 'Y'
							GROUP BY r.release_number, r.project_code) AS r ON a.release_number = r.release_number
			GROUP BY a.release_number
			ORDER BY a.release_number DESC'''

	curs = execute_query(sql)		
	data = curs.fetchall()

	releaseList = []
	
	for row in data:
		release = Release(row[0], row[1])
		releaseList.append(release)
		
	return render_template("releases-main.html", releaseList = releaseList, title=Title('Releases', 'Overview'))

@app.route('/releases/<release>')
def projectsByRelease(release):

	if not logged_in():
		return redirect(url_for('login', url = url_for('projectsByRelease')))

	queryString = parse.unquote(request.query_string.decode("utf-8"))
	parameters = {}

	for parameter in queryString.split('&'):
		if "=" in parameter:
			parameters[parameter.split('=')[0]] = parameter.split('=')[1]

	client = parameters.get('client','')
	projectManager = parameters.get('projectmanager','')
	status = parameters.get('status','')

	filterOptions = FilterOptionsProjects(client, projectManager, status)

	sql = '''SELECT p1.procde, p1.desc, p1.client, COALESCE(risk.risk_level, 'G'), t1.tename, t2.tename, 
	                t3.tename, t4.tename, t5.tename, t6.tename, t7.tename, t8.tename, p1.phase, p1.notes
			  FROM jhcjutil.project AS p1                                       
				INNER JOIN jhcjutil.release_submissions_detail AS r             
						ON p1.procde = r.project_code 
				LEFT OUTER JOIN tearner AS t1 ON p1.owner = t1.teear
				LEFT OUTER JOIN tearner AS t2 ON p1.manger = t2.teear
				LEFT OUTER JOIN tearner AS t3 ON p1.arctct = t3.teear
				LEFT OUTER JOIN tearner AS t4 ON p1.delvry = t4.teear
				LEFT OUTER JOIN tearner AS t5 ON p1.teamld = t5.teear
				LEFT OUTER JOIN tearner AS t6 ON p1.testld = t6.teear
				LEFT OUTER JOIN tearner AS t7 ON p1.prodld = t7.teear
				LEFT OUTER JOIN tearner AS t8 ON p1.anlyst = t8.teear
				LEFT OUTER JOIN (SELECT project_code, MAX(risk_level) AS risk_level FROM jhcjutil.release_submissions_detail 
				WHERE release_number = ? AND release_committee_decision = 'APPROVED' AND risk_level IN ('R', 'A') GROUP BY project_code) AS risk ON p1.procde = risk.project_code							
			WHERE p1.status = 'ACTIVE'                                 
			  AND r.release_number = ?                            
			  AND r.release_committee_decision = 'APPROVED' 
			  AND p1.closed <> 'Y'
			GROUP BY p1.procde, p1.desc, p1.client, risk.risk_level, t1.tename, t2.tename, t3.tename, t4.tename, t5.tename, t6.tename, t7.tename, t8.tename, p1.phase, p1.notes
			ORDER BY p1.procde                                         '''

	curs = execute_query(sql, parms = [release, release])		
	data = curs.fetchall()				
		
	projectList = []		
	clientList = []
	projectManagerList = []
	
	for row in data:
	
		project = Project(row)
		projectList.append(project)
		
		if Client(project.client.strip()) not in clientList:
			client = Client(project.client.strip())
			clientList.append(client)

		if ProjectManager(project.projectManager.strip()) not in projectManagerList and project.projectManager.strip() != "":
			projectManager = ProjectManager(project.projectManager.strip())
			projectManagerList.append(projectManager)				
	
	projectManagerList = sorted(projectManagerList, key=lambda projectManager: projectManager.name)
	clientList = sorted(clientList, key=lambda client: client.name)
	
	return render_template("releases-list.html", projectList = projectList, title=Title('Releases', release), clientList = clientList, filterOptions = filterOptions, projectManagerList = projectManagerList)
	
#############################################
# Projects
#############################################	
@app.route('/projectsearch')
def projectSearch():

	if not logged_in():
		return redirect(url_for('login', url = url_for('projectSearch')))

	query = request.args.get('query')
	query = query.strip().upper()

	sql = '''SELECT DISTINCT procde, desc
				FROM project
			WHERE upper(procde) LIKE '%'  || ?  || '%'
			   OR upper(desc) LIKE '%'  || ? || '%'
			ORDER BY procde'''	
			
	curs = execute_query(sql, parms = [query, query])		
	data = curs.fetchall()

	results = []
	
	for row in data:
		searchJson = {}
		searchJson['id'] = row[0]
		searchJson['label'] = row[1]
		results.append(searchJson)
		
	return json.dumps(results)
	
@app.route('/projects/<projectCode>', methods = ["GET", "POST"])
def projectDetail(projectCode):
	
	if not logged_in():
		return redirect(url_for('login', url = url_for('projectDetail', projectCode='OVERVIEW')))	
	
	if projectCode.upper() == 'OVERVIEW':
		
		if request.method == 'POST':		
			return redirect(url_for('projectDetail', projectCode = request.form['project']))
	
		return render_template("projects-overview.html",title=Title('Projects', 'Overview'))

	sql = '''SELECT p1.procde, p1.desc, p1.client, COALESCE(risk.risk_level, 'G'), t1.tename, t2.tename, 
	                t3.tename, t4.tename, t5.tename, t6.tename, t7.tename, t8.tename, p1.phase, p1.notes
			  FROM jhcjutil.project AS p1                                       
				LEFT OUTER JOIN tearner AS t1 ON p1.owner = t1.teear
				LEFT OUTER JOIN tearner AS t2 ON p1.manger = t2.teear
				LEFT OUTER JOIN tearner AS t3 ON p1.arctct = t3.teear
				LEFT OUTER JOIN tearner AS t4 ON p1.delvry = t4.teear
				LEFT OUTER JOIN tearner AS t5 ON p1.teamld = t5.teear
				LEFT OUTER JOIN tearner AS t6 ON p1.testld = t6.teear
				LEFT OUTER JOIN tearner AS t7 ON p1.prodld = t7.teear
				LEFT OUTER JOIN tearner AS t8 ON p1.anlyst = t8.teear
				LEFT OUTER JOIN (SELECT project_code, MAX(risk_level) AS risk_level FROM jhcjutil.release_submissions_detail 
				WHERE release_committee_decision = 'APPROVED' AND risk_level IN ('R', 'A') GROUP BY project_code) AS risk ON p1.procde = risk.project_code	
			WHERE p1.procde = ? '''

	curs = execute_query(sql, parms = [projectCode])		
	data = curs.fetchall()

	project = Project(data[0])
	
	sql = '''SELECT milestone_desc, milestone_baseline, milestone_current, milestone_rag
				FROM project_milestones
			WHERE project_code = ?'''

	curs = execute_query(sql, parms = [projectCode])		
	data = curs.fetchall()				
		
	milestoneList = []
	
	for row in data:
		milestone = Milestone(row)
		milestoneList.append(milestone)
	
	sql = '''SELECT s.packno, s.app, s.status, s.drp2no 
			  FROM sofpack AS s                                
				INNER JOIN soflnk AS l ON s.packno = l.packno  
				INNER JOIN jobs3 AS j ON l.codex = j.codex     
			WHERE j.proj = ?                             
			ORDER BY s.packno'''
	
	curs = execute_query(sql, parms = [projectCode])		
	data = curs.fetchall()				
		
	softwarePackageList = []
	
	for row in data:
		softwarePackage = SoftwarePackage(row)
		softwarePackageList.append(softwarePackage)	
	
	sql = '''SELECT budget_type, budget_original, budget_revised, budget_actual, budget_forecast 
			  FROM budget                                  
			WHERE project_code = ?                             
			ORDER BY budget_type'''
	
	curs = execute_query(sql, parms = [projectCode])		
	data = curs.fetchall()				
		
	budgetList = []
	
	for row in data:
		budget = Budget(row)
		budgetList.append(budget)	
	
	sql = '''SELECT effort_type, effort_original, effort_revised, effort_actual, effort_forecast 
			  FROM effort                                  
			WHERE project_code = ?                             
			ORDER BY effort_type'''
	
	curs = execute_query(sql, parms = [projectCode])		
	data = curs.fetchall()				
		
	effortList = []
	
	for row in data:
		effort = Effort(row)
		effortList.append(effort)	
		
	return render_template("projects-detail.html",title=Title('Projects', projectCode), project=project, milestoneList=milestoneList, softwarePackageList=softwarePackageList, effortList=effortList, budgetList=budgetList)

@app.route('/knowledge')
def knowledge():
	
	if not logged_in():
		return redirect(url_for('login', url = url_for('knowledge')))	

	return render_template("knowledge-overview.html",title=Title('Knowledge', 'Overview')) 


		