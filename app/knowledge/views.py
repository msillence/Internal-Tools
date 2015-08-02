from flask import Blueprint, render_template, request, url_for, redirect, session
from itertools import groupby
import json

from app.knowledge.models import Language, FunctionalSubArea, FunctionalArea, CodeGuardian
from app.views import logged_in, login, execute_query

mod = Blueprint('knowledge', __name__, url_prefix='/knowledge/')

@mod.route('overview', methods = ["GET"])
def overview():

	return render_template("knowledge/overview.html", title="Knowledge") 	

@mod.route('codeguardians', methods = ["GET"])
def codeGuardians():
	
	sql = '''SELECT d.language_description, b.area_name, c.sub_area_name, a.code_guardian
				FROM sutil.employee_knowledge_area_language AS a
					INNER JOIN sutil.employee_knowledge_area AS b ON a.area_id = b.area_id
					INNER JOIN sutil.employee_knowledge_sub_area AS c ON a.area_id = c.area_id
																	AND a.sub_area_id = c.sub_area_id
					INNER JOIN sutil.employee_knowledge_language AS d ON a.language_id = d.language_id'''
				
	curs = execute_query(sql)		
	data = curs.fetchall()
		
	codeGuardians = []	
	for row in data:
		codeGuardian = CodeGuardian(row.language_description, row.area_name, row.sub_area_name, row.code_guardian)
		codeGuardians.append(codeGuardian)
	
	return render_template("knowledge/code_guardians.html", title="Knowledge", codeGuardians = codeGuardians) 	
	
@mod.route('areas', methods = ["GET"])
def areas():
	
	if not logged_in():
		return redirect(url_for('base.login', url = url_for('knowledge.areas')))		
		
	sql = '''SELECT area_id, area_name FROM sutil.employee_knowledge_area ORDER BY area_name'''
		
	curs = execute_query(sql)
	data = curs.fetchall()
	
	functionalAreas = []
	for row in data:
		functionalArea = FunctionalArea(row.area_id, row.area_name)
		functionalAreas.append(functionalArea)
		
	return render_template("knowledge/areas.html", title="Knowledge", functionalAreas = functionalAreas) 
	
@mod.route('areas/<areaID>')
def areaByID(areaID):	

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('knowledge.areaByID', areaID = areaID)))	
		
	sql = '''SELECT area_name FROM sutil.employee_knowledge_area
			  WHERE area_id = ?'''
			  
	curs = execute_query(sql, parms = [areaID])
	data = curs.fetchone()			
	area_description = data.area_name		
		
	sql = '''SELECT a.sub_area_id, a.sub_area_name, a.wiki_link
				FROM sutil.employee_knowledge_sub_area AS a
			WHERE a.area_id = ?'''
	
	curs = execute_query(sql, parms = [areaID])
	data = curs.fetchall()	
	subAreas = []
	
	for row in data:
		
		subArea = FunctionalSubArea(row.sub_area_id, row.sub_area_name, row.wiki_link, languages = [])		
		subAreas.append(subArea)
		
	return render_template("knowledge/area.html", title="Knowledge", subAreas = subAreas, areaID = areaID, area_description=area_description)	
	
@mod.route('areas/<areaID>/<subAreaID>')
def subAreaByID(areaID, subAreaID):	
	
	sql = '''SELECT area_name FROM sutil.employee_knowledge_area
			  WHERE area_id = ?'''
			  
	curs = execute_query(sql, parms = [areaID])
	data = curs.fetchone()			
	area_description = data.area_name
	
	sql = '''SELECT a.sub_area_id, a.sub_area_name, a.wiki_link
				FROM sutil.employee_knowledge_sub_area AS a
			WHERE a.area_id = ? AND a.sub_area_id = ?'''	
	
	curs = execute_query(sql, parms = [areaID, subAreaID])
	data = curs.fetchone()		
	
	subArea = FunctionalSubArea(data.sub_area_id, data.sub_area_name, data.wiki_link, languages = [])	
	
	sql = '''SELECT a.language_id, c.language_description, COALESCE(b.technical_rating,5) AS technical_rating, a.code_guardian
				FROM sutil.employee_knowledge_area_language AS a
					LEFT OUTER JOIN sutil.employee_knowledge_technical AS b ON a.area_id = b.area_id
																			AND a.sub_area_id = b.sub_area_id
																			AND a.language_id = b.language_id
					INNER JOIN sutil.employee_knowledge_language AS c ON a.language_id = c.language_id 
			WHERE a.area_id = ? AND a.sub_area_id = ? AND b.technical_rating <> 5
			ORDER BY b.technical_rating'''
			
	curs = execute_query(sql, parms=[areaID, subArea.sub_area_id])
	data = curs.fetchall()					
	
	return render_template("knowledge/sub_area.html", title="Knowledge", subArea = subArea, area_description = area_description )
	
@mod.route('update/<int:areaID>')
def update(areaID = 1):
	
	if not logged_in():
		return redirect(url_for('base.login', url = url_for('knowledge.update', areaID = 1)))		
	
	sql = '''SELECT count(*) FROM sutil.employee_knowledge_area'''
	curs = execute_query(sql)
	data = curs.fetchone()
	count = data[0]
	
	if areaID > count:
		return redirect(url_for('knowledge.update', areaID = 1))		
	
	sql = '''SELECT a.area_id, a.area_name, COALESCE(b.functional_rating,'E') AS functional_rating, a.wiki_link
			FROM sutil.employee_knowledge_area AS a
				LEFT OUTER JOIN sutil.employee_knowledge_functional AS b ON b.area_id = a.area_id  
																		AND b.username = ? 
			WHERE a.area_id = ?'''
	
	curs = execute_query(sql, parms = [session['username'], areaID])
	data = curs.fetchall()					
	area = FunctionalArea(data[0].area_id, data[0].area_name, data[0].functional_rating, data[0].wiki_link, sub_areas = [])

	sql = '''SELECT a.sub_area_id, a.sub_area_name, a.wiki_link
				FROM sutil.employee_knowledge_sub_area AS a
			WHERE a.area_id = ?'''
	
	curs = execute_query(sql, parms = [areaID])
	data = curs.fetchall()	
	
	for row in data:
		
		subArea = FunctionalSubArea(row.sub_area_id, row.sub_area_name, row.wiki_link, languages = [])		
		area.sub_areas.append(subArea)
	
	for subArea in area.sub_areas:
		
		sql = '''SELECT a.language_id, c.language_description, COALESCE(b.technical_rating,5) AS technical_rating, a.code_guardian
					FROM sutil.employee_knowledge_area_language AS a
						LEFT OUTER JOIN sutil.employee_knowledge_technical AS b ON a.area_id = b.area_id
																				AND a.sub_area_id = b.sub_area_id
																				AND a.language_id = b.language_id
																				AND b.username = ?
						INNER JOIN sutil.employee_knowledge_language AS c ON a.language_id = c.language_id 
				WHERE a.area_id = ? AND a.sub_area_id = ?'''
				
		curs = execute_query(sql, parms = [session['username'], areaID, subArea.sub_area_id])
		data = curs.fetchall()					
		
		for row in data:
			language = Language(row.language_id, row.language_description, row.code_guardian, row.technical_rating)
			subArea.languages.append(language)
	
	return render_template("knowledge/update.html", area=area, title="Knowledge", areaID=areaID, areaCount=count)
	
@mod.route('post/postf', methods = ["POST"])
def updateFunctionalPost():	
		
	sql = '''MERGE INTO sutil.employee_knowledge_functional AS t 
				  USING (SELECT CAST(? AS CHAR(10)) AS username, CAST(? AS INT) AS area_id, CAST(? AS CHAR(1)) AS functional_rating FROM sysibm.sysdummy1) AS s
				ON s.username = t.username
				AND s.area_id = t.area_id
			  WHEN MATCHED THEN UPDATE SET t.functional_rating = s.functional_rating
			  WHEN NOT MATCHED THEN INSERT (username, area_id, functional_rating) VALUES (s.username, s.area_id, s.functional_rating)'''
	
	execute_query(sql, parms = [session['username'], request.form['area'],request.form['score']])	
	
	return 'ok'
	
@mod.route('post/postt', methods = ["POST"])
def updateTechnicalPost():	
	
	sql = '''MERGE INTO sutil.employee_knowledge_technical AS t 
				  USING (SELECT CAST(? AS CHAR(10)) AS username, CAST(? AS INT) AS area_id, CAST(? AS INT) AS sub_area_id, CAST(? AS INT) AS language_id, CAST(? AS DEC(1)) AS technical_rating FROM sysibm.sysdummy1) AS s
				ON s.username = t.username
				AND s.area_id = t.area_id
				AND s.language_id = t.language_id
				AND s.sub_area_id = t.sub_area_id
			  WHEN MATCHED THEN UPDATE SET t.technical_rating = s.technical_rating
			  WHEN NOT MATCHED THEN INSERT (username, area_id, sub_area_id, language_id, technical_rating) VALUES (s.username, s.area_id, s.sub_area_id, s.language_id, s.technical_rating)'''
	
	execute_query(sql, parms = [session['username'], request.form['area'],  request.form['sub_area'], request.form['language'], request.form['score']])	
	
	return 	'ok'