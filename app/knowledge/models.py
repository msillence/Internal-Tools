class Language():
	
	def __init__(self, id, description, score):
		self.id = id
		self.description = description
		self.score = score
	
class FunctionalSubArea():

	def __init__ (self, area_id, sub_area_id, description, score, area_wiki_link, sub_area_wiki_link, languages):
		self.area_id = area_id
		self.sub_area_id = sub_area_id
		self.description = description
		self.score = score
		self.area_wiki_link = area_wiki_link
		self.sub_area_wiki_link	= sub_area_wiki_link	
		self.languages = languages