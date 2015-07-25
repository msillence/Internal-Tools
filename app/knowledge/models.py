class Language():
	
	def __init__(self, id, description, code_guardian, score = 5):
		self.id = id
		self.description = description
		self.code_guardian = code_guardian
		self.score = score
	
class FunctionalSubArea():

	def __init__ (self, sub_area_id, description, sub_area_wiki_link, languages = []):
		self.sub_area_id = sub_area_id
		self.description = description
		self.sub_area_wiki_link	= sub_area_wiki_link	
		self.languages = languages

class FunctionalArea():
		
	def __init__ (self, area_id, description, score = 'E', wiki_link = None, sub_areas=[]):
		self.area_id = area_id
		self.description = description
		self.score = score
		self.wiki_link = wiki_link
		self.sub_areas = sub_areas