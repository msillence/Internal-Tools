from flask import Blueprint, render_template, request, url_for, redirect, flash
import json

from app.revenue.forms import RevenueForm
from app.revenue.api import *

mod = Blueprint('revenue', __name__, url_prefix='/revenue/')
	
@mod.route('/')
def detail():
	
	return render_template("revenue/detail.html", title="Revenue", revenueList = getAllRevenueEntries())	
	
@mod.route('summarybymonth')
def summaryByMonth():
	
	return render_template("revenue/summary_by_month.html", title="Revenue", revenueSummaryList = getSummaryByMonth())		
	
@mod.route('summarybyyear')
def summaryByYear():
	
	return render_template("revenue/summary_by_year.html", title="Revenue", revenueSummaryList = getSummaryByYear())	
	
@mod.route('add', methods=['GET','POST'])
def add():

	form = RevenueForm()
	
	if request.method == 'POST' and form.validate():
	
		client = form.client.data
		project = form.project.data
		year = form.year.data
		month = form.month.data
		value = form.value.data
			
		createRevenueEntry(client, project, year, month, value)
		flash('Created', 'success')	
		return redirect(url_for('revenue.detail'))
	
	return render_template("miForm.html", title="Revenue", form=form)		
	