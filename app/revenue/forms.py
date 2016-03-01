from wtforms import TextField, SelectField, validators, DecimalField
from flask.ext.wtf import Form
from app.views import execute_query

class RevenueForm(Form):
	client = SelectField('Client', [validators.Required()])
	project = SelectField('Project')
	year = SelectField('Year', [validators.Required()])
	month = SelectField('Month', [validators.Required()])
	value = DecimalField('Value', [validators.Required()], places=2, default=0)
	
	def __init__(self, *args, **kwargs):
		super(RevenueForm, self).__init__(*args, **kwargs)	
	
		results = execute_query('''SELECT id, name
									FROM wapr.jhc_client
								ORDER BY name''')
		
		self.client.choices = [(result.id, result.name) for result in results.fetchall()]
		
		results = execute_query('''SELECT procde, desc                                               
								  FROM project                                                    
								WHERE status NOT IN ('COMPLETE', 'DROPPED', 'REJECT', 'CANCELLED',
													 'REJECTED')                                  
								ORDER BY procde''')
								
		self.project.choices = [("", "")]
		self.project.choices += [(result.procde, result.procde + ' - ' + result.desc) for result in results.fetchall()]
		self.year.choices = [("2016", "2016"), ("2017", "2017"), ("2018", "2018")]
		self.month.choices = [(str(i + 1), str(i + 1)) for i in range(12)]