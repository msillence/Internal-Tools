import os, pyodbc, json, shutil
 
from whoosh.fields import Schema, ID, KEYWORD, TEXT
import whoosh.index as index
from wiki_login import wiki_login

def wiki(writer):
	with wiki_login(os.path.join(os.path.dirname(__file__), 'credentials/credentials.json')) as wiki:
		for i, page in enumerate(wiki.allPages()):
			print('Indexing wiki page: ' + str(i))
			writer.update_document(url="WIKI" + page['title'], title=page['title'],content=wiki.contentByTitle(page['title']),type='WIKI')		

def jobs(writer):			
	sql = '''SELECT codex, CAST(text79 AS CHAR(79) CCSID 1208) AS text                
					FROM jhcjutil.jobscrat          
				ORDER BY codex, pagnum, linnum'''

	with open(os.path.join(os.path.dirname(__file__), 'credentials/export_data_credentials.json')) as data_file:    
		credentials = json.load(data_file)

	connection = pyodbc.connect('DSN=TRACEY;UID=' + credentials['username'] + ';PWD=' + credentials['password'] + ';', autocommit=True)
	cursor = connection.cursor()
	curs = cursor.execute(sql)

	row = curs.fetchone()
	savedJobNumber = None
	text = ''
	while row is not None:

		if savedJobNumber and row.CODEX != savedJobNumber:	
			print('Indexing job:' + str(savedJobNumber))
			writer.update_document(url="JOB" + str(savedJobNumber), title=str(savedJobNumber),content=text,type='JOB')
			text = ''
		
		savedJobNumber = row.CODEX
		text = text + row.TEXT	
		
		row = cursor.fetchone()

def projects(writer):			
	sql = '''SELECT DISTINCT procde, desc
				FROM project'''

	with open(os.path.join(os.path.dirname(__file__), 'credentials/export_data_credentials.json')) as data_file:    
		credentials = json.load(data_file)

	connection = pyodbc.connect('DSN=TRACEY;UID=' + credentials['username'] + ';PWD=' + credentials['password'] + ';', autocommit=True)
	cursor = connection.cursor()
	curs = cursor.execute(sql)

	row = curs.fetchone()
	i = 0
	while row is not None:
		i+= 1
		print('Indexing project:' + str(i))
		writer.update_document(url="PROJECT" + str(row.PROCDE), title=str(row.PROCDE + ' - ' + row.DESC),content=str(row.PROCDE  + ' - ' +  row.DESC),type='PROJECT')
		
		row = cursor.fetchone()		
		
schema = Schema(url=ID(unique=True), title=TEXT(stored=True), content=TEXT(stored=True), type=TEXT(stored=True)) 
 
shutil.rmtree(os.path.join(os.path.dirname(__file__), "index"))
os.mkdir(os.path.join(os.path.dirname(__file__), "index"))
index = index.create_in(os.path.join(os.path.dirname(__file__), "index"), schema)

writer = index.writer()		
wiki(writer)
jobs(writer)
projects(writer)	
writer.commit()	

