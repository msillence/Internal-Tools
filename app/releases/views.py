from flask import Blueprint, render_template, request, url_for, redirect
from urllib import parse

from app.releases.models import Release, FilterOptionsReleases, Project, Client, ProjectManager
from app.views import logged_in, login, execute_query

mod = Blueprint('releases', __name__, url_prefix='/releases')

@mod.route('/')
def overview():

	if not logged_in():
		return redirect(url_for('login', url = url_for('releases.overview')))

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
		
	return render_template("releases/main.html", releaseList = releaseList, title="Releases")

@mod.route('/<release>')
def projectsByRelease(release):

	if not logged_in():
		return redirect(url_for('login', url = url_for('releases.projectsByRelease')))

	queryString = parse.unquote(request.query_string.decode("utf-8"))
	parameters = {}

	for parameter in queryString.split('&'):
		if "=" in parameter:
			parameters[parameter.split('=')[0]] = parameter.split('=')[1]

	client = parameters.get('client','')
	projectManager = parameters.get('projectmanager','')
	status = parameters.get('status','')

	filterOptions = FilterOptionsReleases(client, projectManager, status)

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
	
	return render_template("releases/list.html", projectList = projectList, clientList = clientList, filterOptions = filterOptions, projectManagerList = projectManagerList, title="Releases")
	