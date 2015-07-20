from wtforms import TextField, PasswordField, validators
from flask.ext.wtf import Form

class LoginForm(Form):
	username = TextField('Username', [validators.Required()])
	password = PasswordField('Password', [validators.Required()])