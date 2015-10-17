import os, pyodbc, json
 
from whoosh.fields import Schema, ID, KEYWORD, TEXT
import whoosh.index as index
from wiki_login import wiki_login

def wiki(writer):
	with wiki_login('credentials.json') as wiki:
		for i, page in enumerate(wiki.allPages()):
			print('Indexing wiki page: ' + str(i))
			writer.update_document(title=page['title'],content=wiki.contentByTitle(page['title']),type='WIKI')		

def jobs(writer):			
	sql = '''SELECT codex, CAST(text79 AS CHAR(79) CCSID 1208) AS text                
					FROM jhcjutil.jobscrat          
				ORDER BY codex, pagnum, linnum'''

	with open('credentials/export_data_credentials.json') as data_file:    
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
			writer.update_document(title=str(savedJobNumber),content=text,type='JOB')
			text = ''
		
		savedJobNumber = row.CODEX
		text = text + row.TEXT	
		
		row = cursor.fetchone()

def projects(writer):			
	sql = '''SELECT DISTINCT procde, desc
				FROM project'''

	with open('credentials/export_data_credentials.json') as data_file:    
		credentials = json.load(data_file)

	connection = pyodbc.connect('DSN=TRACEY;UID=' + credentials['username'] + ';PWD=' + credentials['password'] + ';', autocommit=True)
	cursor = connection.cursor()
	curs = cursor.execute(sql)

	row = curs.fetchone()
	i = 0
	while row is not None:
		i+= 1
		print('Indexing project:' + str(i))
		writer.update_document(title=str(row.PROCDE + ' - ' + row.DESC),content=str(row.PROCDE  + ' - ' +  row.DESC),type='PROJECT')
		
		row = cursor.fetchone()		
		
schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True), type=TEXT(stored=True))
 
if not os.path.exists("index"):
    os.mkdir("index")

if not index.exists_in("index"):
	index = index.create_in("index", schema)
else:
	index = index.open_dir("index")

writer = index.writer()		
wiki(writer)
jobs(writer)
projects(writer)	
writer.commit()	

