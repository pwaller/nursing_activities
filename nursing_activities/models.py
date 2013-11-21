from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Float,
    Text,
    DateTime,
    )

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class MakeByName(object):
    @classmethod
    def get(cls, name, **kwargs):
        result = DBSession.query(cls).filter(cls.name == name).first()
        if result is None:
            result = cls()
            result.name = name
            DBSession.add(result)
            for key, value in kwargs.iteritems():
                setattr(result, key, value)
        return result

class Activity(MakeByName, Base):
    __tablename__ = 'activities'
    name = Column(Text, primary_key=True)

    def __repr__(self):
        return "<Activity name={0}>".format(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def unit(self):
        return {
            "Assessment": "Scripts",
            "Dissertation supervision": "Students",
            "Leadership": "Role",
            "Teaching":"Hours",
            "Academic Advisement": "Students",
            "Recruitment": "Hours",
        }[self.name]
        

class Semester(MakeByName, Base):
    __tablename__ = 'semesters'
    name = Column(Text, primary_key=True)

class ActivityItem(Base):
    __tablename__ = 'activity_item'

    id = Column(Integer, primary_key=True)

    time = Column(DateTime)
    #date = Column(Date)
    #day_of_week = Column(Text)

    duration = Column(Float)
    tarrif = Column(Float)
    
    # total_time = Column(Float) (duration * tarrif)

    activity_id = Column(Text, ForeignKey("activities.name"))
    activity = relationship("Activity", backref="items")

    staff_id = Column(Text, ForeignKey("staff.name"))
    staff = relationship("Staff", backref="activities")

    course_id = Column(Text, ForeignKey("courses.name"))
    course = relationship("Course", backref="all_activites")

    topic_id = Column(Text, ForeignKey("topics.name"))
    topic = relationship("Topic", backref="activity_items")

    category = Column(Text)

    def __repr__(self):
        return u"<Item staff={0} activity={1} course={2} duration={3}>".format(
            self.staff, self.activity, self.course, self.duration)

class StaffActivities(object):
    def __init__(self, staff, course, activities):
        self.staff = staff
        self.course = course
        self.activities = activities

class Staff(MakeByName, Base):
    __tablename__ = 'staff'
    name = Column(Text, primary_key=True)

    division = Column(Text)
    contract_type = Column(Text)
    full_time_equivalent = Column(Float)

    @property
    def grand_total(self):
        return sum(a.tarrif*a.duration for a in self.activities)

    @property
    def tbc(self):
        return DBSession.query(Staff).filter(Staff.name.like(self.name + "%confirmed%")).all()

    def __repr__(self):
        return u"<Staff name={0}>".format(self.name)
        
    def __getitem__(self, key):
    
        try:
            course = DBSession.query(Course).filter_by(name=key).one()
        except NoResultFound:
            try:
                course = DBSession.query(Course).filter_by(unit_title=key).one()
            except NoResultFound:
                raise RuntimeError("No such course: {0}".format(key))
        
        activities = [a for a in self.activities if a.course == course]
        return StaffActivities(self, course, activities)

class Course(MakeByName, Base):
    __tablename__ = 'courses'
    name = Column(Text, primary_key=True)
    cs_code = Column(Text)

    cohort_id = Column(Text, ForeignKey('cohorts.name'))
    cohort = relationship("Cohort", backref="courses")

    def activities(self, staff):
        return [a for a in self.all_activites if a.staff is staff]

    #activity_items = relationship("ActivityItem")


    #topic_id = Column(Text, ForeignKey("topics.name"))
    #topics = relationship("Topic", secondary="activity_item")
    #topics = association_proxy('activity_items', 'topic')

    def __repr__(self):
        return "<Course name={0} cs_code={1} cohort={2}>".format(self.name, self.cs_code, self.cohort)


    def __lt__(self, other):
        return self.cs_code < other.cs_code

class Topic(MakeByName, Base):
    __tablename__ = 'topics'
    name = Column(Text, primary_key=True)

class Programme(MakeByName, Base):
    __tablename__ = 'programmes'
    name = Column(Text, primary_key=True)

class Cohort(MakeByName, Base):
    __tablename__ = 'cohorts'
    name = Column(Text, primary_key=True)
    #programme = Column(Text)

    programme_id = Column(Text, ForeignKey('programmes.name'))
    programme = relationship("Programme", backref="cohorts")

    def __repr__(self):
        return "<Cohort name={0} programme={1}>".format(self.name, self.programme)
