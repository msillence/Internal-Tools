from flask import Blueprint, render_template, request, url_for, redirect
import json

from app.projects.models import Project, Milestone, SoftwarePackage, Budget, Effort
from app.views import execute_query

mod = Blueprint('projects', __name__, url_prefix='/projects/')
	
@mod.route('<projectCode>')
def projectDetail(projectCode):

	sql = '''SELECT p1.procde, p1.desc, p1.client, COALESCE(risk.rag, 'G'), t1.tename, t2.tename, 
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
				LEFT OUTER JOIN (SELECT r2.procde AS procde,
									r2.entry,
									r2.rag AS rag,
									r2.summary AS summary,
									r2.notes AS notes
								FROM b6009822.jhcjutil.PROJRAG AS r2
								INNER JOIN (
									SELECT procde,
										max(entry) AS entry
									FROM b6009822.jhcjutil.PROJRAG
									GROUP BY procde
									) AS r3 ON r2.procde = r3.procde AND r2.entry = r3.entry) AS risk ON risk.procde = p1.procde	
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
	
	sql = '''SELECT s.packno, s.app, s.status, s.drp2no, s.dripno 
			  FROM sofpack AS s                                
				INNER JOIN soflnk AS l ON s.packno = l.packno  
				INNER JOIN jobs3 AS j ON l.codex = j.codex     
			WHERE j.proj = ?  
			GROUP BY s.packno, s.app, s.status, s.drp2no, s.dripno
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
	