
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

from app.views import mod as baseModule
app.register_blueprint(baseModule)

from app.files.views import mod as filesModule
app.register_blueprint(filesModule)

from app.jobs.views import mod as jobsModule
app.register_blueprint(jobsModule)

from app.projects.views import mod as projectsModule
app.register_blueprint(projectsModule)

from app.releases.views import mod as releasesModule
app.register_blueprint(releasesModule)

from app.knowledge.views import mod as knowledgeModule
app.register_blueprint(knowledgeModule)