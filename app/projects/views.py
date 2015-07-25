from flask import Blueprint, render_template, request, url_for, redirect
import json

from app.projects.models import Project, Milestone, SoftwarePackage, Budget, Effort
from app.views import logged_in, login, execute_query

mod = Blueprint('projects', __name__, url_prefix='/projects/')

@mod.route('search')
def projectSearch():

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('projects.projectSearch')))

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
	
@mod.route('overview', methods = ["GET", "POST"])
def overview():	
	
		if request.method == 'POST':		
			return redirect(url_for('projects.projectDetail', projectCode = request.form['project']))
	
		return render_template("projects/overview.html", title="Projects")	
	
@mod.route('byprojectcode/<projectCode>')
def projectDetail(projectCode):
	
	if not logged_in():
		return redirect(url_for('base.login', url = url_for('projects.overview')))

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
		
	return render_template("projects/detail.html", project=project, milestoneList=milestoneList, softwarePackageList=softwarePackageList, effortList=effortList, budgetList=budgetList, title="Projects")	
	