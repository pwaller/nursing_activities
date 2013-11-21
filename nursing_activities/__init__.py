from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from sqlalchemy.orm.exc import NoResultFound

from .models import (
    Base,
    Course,
    DBSession,
    Staff,
    )

class Home(object):
    __parent__ = __name__ = None

    def __init__(self, *args):
        self.args = args

    def __getitem__(self, key):

        if key.endswith(".html"):
            key = key[:-len(".html")]

        if key == "courses":
            return Courses()
        if key == "divisions":
            return Divisions()

        return DBSession.query(Staff).filter(Staff.name == key).one()


class Courses(object):
    __parent__ = Home
    __name__ = "courses"

    def __getitem__(self, key):
        return DBSession.query(Course).filter(Course.name == key).one()

class Divisions(object):
    __parent__ = Home
    __name__ = "divisions"

    def __getitem__(self, key):
        if key.endswith(".html"):
            key = key[:-len(".html")]
            
        return Division(key)
        
class Division(object):
    def __init__(self, division):
        self.name = division        

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings, root_factory=Home)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()

    return config.make_wsgi_app()
