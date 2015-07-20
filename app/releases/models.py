class Release():		

	def __init__(self, releaseNumber, projectCount):		
		self.releaseNumber = releaseNumber
		self.projectCount = projectCount
		
class FilterOptionsReleases:

	def __init__(self, client, projectManager, status):

		self.client = client
		self.projectManager = projectManager
		self.status = status
		
class Project():		

	def __init__(self, row):
		self.projectCode = row[0].strip()
		self.description = row[1]
		self.client = row[2]
		self.riskLevel = row[3]
		self.owner = row[4]
		self.projectManager = row[5]
		self.designer = row[6]
		self.deliveryManager = row[7]
		self.teamLeader = row[8]
		self.testLeader = row[9]
		self.productLeader = row[10]
		self.businessAnalyst = row[11]
		self.phase = row[12]
		self.notes = '<br>'.join(row[13][i:i+64] for i in range(0, len(row[13].strip()), 64))
		
class Client:

	def __init__(self, name, numberOfJobs = 0):
		self.name = name
		self.numberOfJobs = numberOfJobs
		
	def __eq__(self, other):
		return self.name == other.name
		
class ProjectManager:

	def __init__(self, name):
		self.name = name		

	def __eq__(self, other):
		return self.name == other.name