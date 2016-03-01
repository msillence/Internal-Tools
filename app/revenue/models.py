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

class Milestone():		

	def __init__(self, row):
		self.description = row[0]
		self.baseline = row[1]
		self.current = row[2]
		self.riskLevel = row[3]

class SoftwarePackage():

	def __init__(self, row):
		self.number = row[0]
		self.application = row[1]
		self.status = row[2]
		self.approvedRelease = row[3]
		self.actualRelease = row[4]		

class Budget():

	def __init__(self, row):
		self.type = row[0]
		self.original = u"\xA3{:,.0f}".format(row[1])
		self.revised = u"\xA3{:,.0f}".format(row[2])
		self.actual = u"\xA3{:,.0f}".format(row[3])	
		self.forecast = u"\xA3{:,.0f}".format(row[4])
	
class Effort():

	def __init__(self, row):
		self.type = row[0]
		self.original = row[1]
		self.revised = row[2]
		self.actual = row[3]	
		self.forecast = row[4]
		
class Release():		

	def __init__(self, releaseNumber, projectCount):		
		self.releaseNumber = releaseNumber
		self.projectCount = projectCount