class Release():		

	def __init__(self, releaseNumber, projectCount):		
		self.releaseNumber = releaseNumber
		self.projectCount = projectCount
		
class FilterOptionsReleases:

	def __init__(self, client, projectManager, status, sitCycle, devTeamLeader, testLead):

		self.client = client
		self.projectManager = projectManager
		self.status = status
		self.sitCycle = sitCycle
		self.devTeamLeader = devTeamLeader
		self.testLead = testLead
		
class Project():		

	def __init__(self, row):
		self.projectCode = row[0].strip()
		self.sitCycle = row[1]
		self.description = row[2]
		self.client = row[3]
		self.riskLevel = row[4]
		self.owner = row[5]
		self.projectManager = row[6]
		self.designer = row[7]
		self.deliveryManager = row[8]
		self.teamLeader = row[9]
		self.testLeader = row[10]
		self.productLeader = row[11]
		self.businessAnalyst = row[12]
		self.phase = row[13]
		self.notes = '<br>'.join(row[14][i:i+64] for i in range(0, len(row[14].strip()), 64))
		
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
		
class DevTeamLead:

	def __init__(self, name):
		self.name = name		

	def __eq__(self, other):
		return self.name == other.name

class TestLead:

	def __init__(self, name):
		self.name = name		

	def __eq__(self, other):
		return self.name == other.name		