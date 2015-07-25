from flask import Blueprint, render_template, request, url_for, redirect
from urllib import parse
import json, time, datetime

from app.jobs.models import Job, Area, Priority, Client, Status, FilterOptionsJobs
from app.views import logged_in, login, execute_query
from app.models import MyEncoder

mod = Blueprint('jobs', __name__, url_prefix='/jobs/')
			
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

@mod.route("joblist", methods = ["GET"])
def job_list():

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('jobs.job_list')))	

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
	
	return render_template("jobs/list.html", jobList = jobList, clientList = clientList, functionalAreaList = functionalAreaList, statusList = statusList, filterOptions = filterOptions, title="FST Jobs")

@mod.route("overview", methods = ["GET"])
def overview():

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('jobs.overview')))	

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
	
		
	return render_template("jobs/overview.html", areaList = areaList, priorityList = getPriorityData(), clientList=clientList, statusList=statusList, total=total, monthlyJobsOpened=monthlyJobsOpened, monthlyJobsClosed=monthlyJobsClosed, monthlyAverageResolution=monthlyAverageResolution, quarterlyJobsOpened=quarterlyJobsOpened, quarterlyJobsClosed=quarterlyJobsClosed, quarterlyAverageResolution=quarterlyAverageResolution, title="FST Jobs")

@mod.route("history", methods = ["GET"])
def history():	

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('jobs.history')))	
		
	return render_template("jobs/history.html", title="FST Jobs")

@mod.route("history_chart", methods = ["GET"])
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
	
@mod.route("job", methods = ["GET"])	
@mod.route("job/<job>", methods = ["GET"])
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
	