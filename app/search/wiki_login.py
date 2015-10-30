import requests
import json

class wiki_login:
	def __init__(self, credentialsFile):
		self._get_credentials(credentialsFile)
		self.session = requests.session()

	def _get_credentials(self, credentialsFile):
		credentialsPath = credentialsFile
		with open(credentialsPath) as credentials:
			credentialsObject = json.loads(credentials.read())
			self.get_credentials_from_object(credentialsObject)
			
	def get_credentials_from_object(self, credentialsObject):
		self.url = credentialsObject['url']
		self.lgname = credentialsObject['lgname']
		self.lgpassword = credentialsObject['lgpassword']
		self.bot = credentialsObject['bot']

	def __enter__(self):
		request = {'action':'login', 'format':'json'}
		request['lgname'] = self.lgname
		request['lgpassword'] = self.lgpassword
		result = self.session.post(self.url, params=request).json()
		request['lgtoken'] = result['login']['token']
		result = self.session.post(self.url, params=request).json()
		print('logged in')
		return self

	def __exit__(self, type, value, traceback):
		request = {'action':'logout', 'format':'json'}
		self.session.post(self.url, params=request)
		print('logged out')

	def _editToken(self):
		try:
			return self.editToken
		except AttributeError:
			editTokenRequest = {'action':'tokens', 'format':'json'}
			self.editToken = self.session.get(self.url, params=editTokenRequest).json()['tokens']['edittoken']
			return self.editToken

	def _listquery(self, request):
		request['action'] = 'query'
		request['format'] = 'json'
		request['prop'] = 'revisions'
		request['rvprop'] = 'content'
		lastContinue = {'continue': ''}
		while True:
			req = request.copy()
			req.update(lastContinue)
			result = self.session.get(self.url, params=req).json()
			if 'error' in result: print(result['error'])
			if 'warnings' in result: print(result['warnings'])
			if 'query' in result:
				for page in result['query']['querypage']['results']:
					yield page
			if 'continue' not in result: break
			lastContinue = result['continue']

	def _content(self, request):
		request['action'] = 'query'
		request['format'] = 'json'
		request['prop'] = 'revisions'
		request['rvprop'] = 'content'
		result = self.session.get(self.url, params=request).json()
		for page in result['query']['pages']:
			return result['query']['pages'][page]['revisions'][0]['*'].strip()

	def _lastRevision(self, request):
		request['action'] = 'query'
		request['format'] = 'json'
		request['prop'] = 'revisions'
		request['rvlimit'] = 500
		request['rvprop'] = 'user|timestamp'
		result = self.session.get(self.url, params=request).json()
		for page in result['query']['pages']:
			lastRevision = {}
			userAndTime = result['query']['pages'][page]['revisions'][0]
			lastRevision['title'] = request['titles']
			lastRevision.update(userAndTime)
			return lastRevision

	def _lastMajorRevision(self, request):
		request['action'] = 'query'
		request['format'] = 'json'
		request['prop'] = 'revisions'
		request['rvlimit'] = 500
		request['rvprop'] = 'user|timestamp|flags'
		lastcontinue = {''}
		result = self.session.get(self.url, params=request).json()
		for pageid in result['query']['pages']:
			page = result['query']['pages'][pageid]
			for revision in page['revisions']:
				if 'minor' not in revision: return revision

	def _list(self, request):
		request['action'] = 'query'
		request['format'] = 'json'
		request['prop'] = 'revisions'
		request['rvlimit'] = 500
		request['rvprop'] = 'content'
		request['apfilterredir'] = 'nonredirects'
		lastContinue = {'continue': ''}
		while True:
			req = request.copy()
			req.update(lastContinue)
			result = self.session.get(self.url, params=req).json()
			if 'error' in result: print(result['error'])
			if 'warnings' in result: print(result['warnings'])
			if 'query' in result:
				for page in result['query']['allpages']:
					yield page
			if 'continue' not in result: break
			lastContinue = result['continue']

	def shortestPages(self):
		return self._listquery({'list':'querypage', 'qppage':'Shortpages'})

	def allPages(self):
		return self._list({'list':'allpages'})

	def contentByTitle(self, title):
		request = {'titles': title}
		return self._content(request)

	def lastRevisionByTitle(self, title):
		request = {'titles': title}
		return self._lastRevision(request)

	def lastMajorRevisionByTitle(self, title):
		request = {'titles': title}
		return self._lastMajorRevision(request)

	def pageCategories(self, title):
		request = {
		'action':'query',
		'format':'json',
		'prop':'categories',
		'cllimit':500,
		'titles':title
		}
		result = self.session.get(self.url, params=request).json()['query']['pages']
		try:
			result = result[result.keys()[0]]['categories']
			for category in result:
				yield category['title']
		except:
			iter(())

	def pageTemplates(self, title):
		request = {
		'action':'query',
		'format':'json',
		'prop':'templates',
		'tllimit':500,
		'titles':title
		}
		result = self.session.get(self.url, params=request).json()['query']['pages']
		try:
			result = result[result.keys()[0]]['templates']
			for category in result:
				yield category['title']
		except:
			iter(())

	def isPageInCategory(self, title, category):
		if not category.startswith('Category:'):
			raise ValueError("Category {!s} not valid; should start with 'Category:'.".format(category))
		cats = self.pageCategories(title)
		for cat in cats:
			if cat == category: return True
		return False

	def pageHasTemplate(self, title, template):
		if not template.startswith('Template:'):
			raise ValueError("Template {!s} not valid; should start with 'Template:'.".format(template))
		allTemplates = self.pageTemplates(title)
		for tem in allTemplates:
			if tem == template: return True
		return False

	def isPageMarkedForDeletion(self, title):
		cats = self.pageCategories(title)
		for cat in cats:
			if cat == 'Category:Flagged for deletion': return True
			if cat == 'Category:Due for deletion': return True
		return False

	def markPageForDeletion(self, title, summary):
		if not isPageMarkedForDeletion(title):
			wiki._prependTextToPage(title, '{{cmbox|type=delete}}', summary, minor=True)

	def _prependTextToPage(self, pageTitle, text, summary, minor):
		request = {
			'action':'edit',
			'format':'json',
			'title':pageTitle,
			'token':self._editToken(),
			'summary':summary,
			'prependtext':text
		}
		if minor:
			request['minor'] = ''
		else:
			request['notminor'] = ''
		if self.bot:
			request['bot'] = ''
		print(request)
		result = self.session.post(self.url, params=request).json()
