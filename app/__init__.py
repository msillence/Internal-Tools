
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

from app.views import mod as baseModule
app.register_blueprint(baseModule)

from app.files.views import mod as filesModule
app.register_blueprint(filesModule)

from app.projects.views import mod as projectsModule
app.register_blueprint(projectsModule)

from app.releases.views import mod as releasesModule
app.register_blueprint(releasesModule)

from app.search.views import mod as searchModule
app.register_blueprint(searchModule)

from app.revenue.views import mod as revenueModule
app.register_blueprint(revenueModule)