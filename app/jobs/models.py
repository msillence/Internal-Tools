class Job:

	def __init__(self, number, client, shortText,  longText, assignedTo, status, priority, functionalArea):
		self.number = number
		self.client = client
		self.shortText = shortText
		self.longText = longText
		self.assignedTo = assignedTo
		self.status = status
		self.priority = priority
		self.functionalArea = functionalArea

class Area:

	def __init__(self, functionalArea, numberOfJobs = 0):
		self.functionalArea = functionalArea
		self.numberOfJobs = numberOfJobs

class Priority:

	def __init__(self, level, numberOfJobs):
		self.level = level
		self.numberOfJobs = numberOfJobs

class Client:

	def __init__(self, name, numberOfJobs = 0):
		self.name = name
		self.numberOfJobs = numberOfJobs
		
	def __eq__(self, other):
		return self.name == other.name
		
class Status:

	def __init__(self, name, numberOfJobs = 0):
		if name == 'A':
			self.name = 'Awaiting Assignment'
		elif name == 'B':
			self.name = 'Assigned'
		elif name == 'C':
			self.name = 'Closed'
		elif name == 'E':
			self.name = 'Fixed in Client Environment'
		elif name == 'H':
			self.name = 'On Hold'
		elif name == 'K':
			self.name = 'Requires Code Fix'
		elif name == 'T':
			self.name = 'In Test'
		elif name == 'W':
			self.name = 'Waiting'
		else:
			self.name = name
		
		self.numberOfJobs = numberOfJobs	
		self.letter = name
		
class FilterOptionsJobs:

	def __init__(self, priority, client, assignedTo, jobText, functionalArea, status):

		self.priority = priority
		self.client = client
		self.assignedTo = assignedTo
		self.jobText = jobText
		self.functionalArea = functionalArea
		self.status = status