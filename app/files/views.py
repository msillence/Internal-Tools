from flask import Blueprint, url_for, redirect, render_template, request
from app.files.models import Table
from app.views import logged_in, login

mod = Blueprint('files', __name__, url_prefix='/files/')

@mod.route('<library>/<table>/')
def view(library, table):

	if not logged_in():
		return redirect(url_for('login', url = url_for('files.view', library=library, table=table)))	

	tableInstance = Table(library, table)
	
	return render_template("files/main.html", columns = tableInstance.columns, library = library, table = table, title= 'Files')		
	
@mod.route('<library>/<table>/data')
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