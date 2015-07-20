from flask import Blueprint, render_template, request, url_for, redirect, session
from itertools import groupby
import json

from app.knowledge.models import Language, FunctionalSubArea
from app.views import logged_in, login, execute_query

mod = Blueprint('knowledge', __name__, url_prefix='/knowledge')

@mod.route('/')
def overview():
	
	if not logged_in():
		return redirect(url_for('login', url = url_for('knowledge.overview')))		
		
	return render_template("knowledge/overview.html", title="Knowledge") 
	
@mod.route('/update')
def update():
	
	if not logged_in():
		return redirect(url_for('login', url = url_for('knowledgeUpdate')))		
	
	sql = '''SELECT a.area_name || ' - ' || f.sub_area_name, b.area_id, b.sub_area_id, COALESCE(e.functional_rating, 'E'), 
	                b.language_id, c.language_description, COALESCE(d.technical_rating, 5), a.wiki_link, f.wiki_link
			FROM sutil.employee_knowledge_area_language AS b
			   INNER JOIN  sutil.employee_knowledge_area AS a ON a.area_id = b.area_id
			   INNER JOIN sutil.employee_knowledge_sub_area AS f ON b.area_id = f.area_id 
			                                                     AND b.sub_area_id = f.sub_area_id
			   INNER JOIN  sutil.employee_knowledge_language AS c ON b.language_id = c.language_id
			   LEFT OUTER JOIN sutil.employee_knowledge_technical AS d ON b.area_id = d.area_id
			                                                           AND b.language_id = d.language_id
																	   AND d.username = ?
			   LEFT OUTER JOIN sutil.employee_knowledge_functional AS e ON b.area_id = e.area_id  
			                                                           AND e.username = ?
			ORDER BY a.area_name || f.sub_area_name'''
	
	curs = execute_query(sql, parms = [session['username'], session['username']])
	data = curs.fetchall()
	
	areaList = []
	for key, row in groupby(data, lambda x:x[0]):
	
		groupedArea = list(row)
		
		languages = []		
		for entry in groupedArea:
			languages.append(Language(entry[4], entry[5], entry[6]))
			
		areaList.append(FunctionalSubArea(groupedArea[0][1], groupedArea[0][2], groupedArea[0][0], groupedArea[0][3], groupedArea[0][7], groupedArea[0][8], languages))	
	
	return render_template("knowledge/update.html", areaList=areaList, title="Knowledge")
	
@mod.route('/update/postf', methods = ["POST"])
def updateFunctionalPost():	
		
	sql = '''MERGE INTO sutil.employee_knowledge_functional AS t 
				  USING (SELECT CAST(? AS CHAR(10)) AS username, CAST(? AS INT) AS area_id, CAST(? AS INT) AS sub_area_id, CAST(? AS CHAR(1)) AS functional_rating FROM sysibm.sysdummy1) AS s
				ON s.username = t.username
				AND s.area_id = t.area_id
				AND s.sub_area_id = t.sub_area_id
			  WHEN MATCHED THEN UPDATE SET t.functional_rating = s.functional_rating
			  WHEN NOT MATCHED THEN INSERT (username, area_id, sub_area_id, functional_rating) VALUES (s.username, s.area_id, s.sub_area_id, s.functional_rating)'''
	
	execute_query(sql, parms = [session['username'], request.form['area'], request.form['sub_area'],request.form['score']])	
	
	return 'ok'
	
@mod.route('/update/postt', methods = ["POST"])
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