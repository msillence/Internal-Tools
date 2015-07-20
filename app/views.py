from flask import Blueprint, render_template, request, Response, session, url_for, flash, redirect
import pyodbc

from app.forms import LoginForm

mod = Blueprint('base', __name__)

def logged_in():

	if 'username' not in session or 'password' not in session or session['username'] == None or session['password'] == None:
		return False
		
	try:
		execute_query('SELECT * FROM sysibm.sysdummy1')
	except pyodbc.Error as err:
		if 'username' in session:
			session['username'] = None
		if 'password' in session:	
			session['password'] = None
		return False
		
	return True			
	
def execute_query(sql, parms = []):

	connection_string = 'DSN=TRACEY;UID=' + session['username'] + ';PWD=' + session['password'] + ';CHARSET=UTF8;'
	connection        = pyodbc.connect(connection_string, autocommit=True)
	cursor            = connection.cursor()
	return cursor.execute(sql, parms)
		
@mod.route('/login', methods=['GET', 'POST'])
def login():

	url = request.args.get('url')
	
	form = LoginForm()
	
	if form.validate_on_submit():
	
		session['username'] = form.username.data.upper()
		session['password'] = form.password.data
		
		if logged_in() and url:	
			session.permanent = True
			return redirect(url)
		elif logged_in():
			session.permanent = True
			return redirect(url_for('jobs.overview'))		
		else:
			flash('Invalid username or password')
		
	return render_template("login.html", form=form, url=url)
	