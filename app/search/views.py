from flask import Blueprint, Flask, render_template, url_for, request, flash, redirect, Response, send_from_directory, send_file
from flask.views import MethodView
from whoosh.fields import Schema
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from app import app

mod = Blueprint('search', __name__, template_folder='templates', url_prefix='/search/')

class Search(MethodView):

	def get(self):
	
		wikiResults = None
		jobResults = None
		projectResults = None	
	
		if 'searchScope' in request.args and 'searchTerm' in request.args:	
			
			searchTerm = request.args.get('searchTerm')	
			searchScope = request.args.get('searchScope')	
			index = open_dir('app/search/index')
			parser = QueryParser("content", schema=index.schema)
				
			with index.searcher() as searcher:
			
				if searchScope in ['everything', 'wiki']:
					wikiResults = [{'title':result['title'], 'url':'http://jhcwiki.jhc.co.uk/wiki/index.php/' + result['title'].replace(' ', '_')} for result in searcher.search(parser.parse(searchTerm), limit=200) if result['type'] == 'WIKI']
				
				if searchScope in ['everything', 'jobs']:
					jobResults = [{'title':result['title'], 'url':''} for result in searcher.search(parser.parse(searchTerm), limit=200) if result['type'] == 'JOB']

				if searchScope in ['everything', 'projects']:	
					projectResults = [{'title':result['title'], 'url':url_for('projects.projectDetail', projectCode = result['title'].split('-')[0].strip())} for result in searcher.search(parser.parse(searchTerm), limit=200) if result['type'] == 'PROJECT']
		else:
			searchTerm = ''	
			searchScope = 'everything'
			
		return render_template('search/search.html', wikiResults=wikiResults, jobResults=jobResults , projectResults=projectResults, searchTerm=searchTerm, searchScope=searchScope, title="Search")	
		
mod.add_url_rule('/', view_func=Search.as_view('overview'))
