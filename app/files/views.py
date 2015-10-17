from flask import Blueprint, url_for, redirect, render_template, request, flash
from app.files.models import Table
from app.views import logged_in, login

mod = Blueprint('files', __name__, url_prefix='/files/')

@mod.route('/', methods=['POST', 'GET'])
def overview():

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('files.overview')))	
		
	if 'library' in request.form:
		library=request.form['library']
	else:
		library = None
		
	if 'file' in request.form:
		file=request.form['file']
	else:
		file = None		
		
	if request.method == 'POST' and library and file:
		return redirect(url_for('files.view', library = library, table = file))
	elif request.method == 'POST':
		flash('Please enter both a library and file name')
		
	return render_template("files/overview.html", title= 'Files', library=library, file=file)	

@mod.route('<library>/<table>/')
def view(library, table):

	if not logged_in():
		return redirect(url_for('base.login', url = url_for('files.view', library=library, table=table)))	

	try:	
		tableInstance = Table(library, table)
	except:
		flash('This table does not exist')
		return redirect(url_for('files.overview'))
	
	return render_template("files/main.html", columns = tableInstance.columns, library = library, table = table, title= 'Files')		
	
@mod.route('<library>/<table>/data')
def get_data(library, table):			
		 	
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