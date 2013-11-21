from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.sql import distinct
from sqlalchemy.exc import DBAPIError

from nursing_activities import Home, Courses, Divisions, Division

from .models import (
    Activity,
    ActivityItem,
    Course,
    DBSession,
    Staff,
    StaffActivities,
    )


@view_config(context=Home, renderer='templates/home.pt')
def home(context, request):
    return {'staff': DBSession.query(Staff).order_by(Staff.name).all()}


@view_config(context=StaffActivities, renderer='templates/staff_activities.pt')
def staff_activities(context, request):
    return {'staff': context.staff, 'course': context.course,
        'activities': context.activities}


@view_config(context=Courses, renderer='templates/courses.pt')
def courses(courses, request):
    from pyramid.url import urlencode
    return {
    "urlencode": urlencode,
    "courses": 
        DBSession
        .query(Course)
        .join(ActivityItem)
        .join(Activity)
        .filter(ActivityItem.activity.has(Activity.name == "Teaching"))
    }
        #Course.has(ActivityItem.activity.name == "Teaching")).all()}

@view_config(context=Course, renderer='templates/timetable.pt')
def timetable(course, request):
    timetable = (
        DBSession
        .query(ActivityItem)
        .join(Course, Activity)
        .filter(ActivityItem.course == course)
        .filter(ActivityItem.activity_id == "Teaching")
        .order_by(ActivityItem.time)
        )
    return {"timetable": timetable}

def group_by(lst, *criteria):

    if not criteria:
        return list(lst)

    import itertools

    first, more = criteria[0], criteria[1:]

    result = {}
    for key, values in itertools.groupby(sorted(lst, key=first), key=first):
        result[key] = group_by(values, *more)

    return result

def build_staff_view(activities):

    rows = []

    total = sum(a.tarrif*a.duration for a in activities)

    rows.append((
        {'style': 'background: #ddd; border-bottom: 10px solid white;'}, 
        '<td colspan="3"><h2>Grand Total</h2></td><td style="text-align:right; font-weight:bold;">{}</td>'.format(total)))

    by_activity = group_by(activities, lambda a: a.activity, lambda a: a.course)

    for activity_type, courses in sorted(by_activity.iteritems()):
        rows.append((
            {'style': 'background: #ddd'}, 
            ('<td colspan="2"><h3>{}</h3></td><td style="margin-right: 1em;">{}</td><td>Adjusted</td>'
            ).format(
                activity_type.name, activity_type.unit())))


        for course, course_activities in sorted(courses.iteritems()):

            total_hours = sum(activity.duration*activity.tarrif for activity in course_activities)

            code = course.cs_code if course.cs_code else "&ndash;"

            content = (
                '<td style="font-weight: bold; font-size: 75%; text-align: center;">{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
            ).format(
                code, 
                course.name,
                sum(a.duration for a in course_activities),
                total_hours)

            rows.append(({'style': 'background: #eee'}, content))

            from itertools import groupby
            by_cat = dict(groupby(sorted(course_activities, key=lambda c: c.category), lambda a: a.category))


            by_cat = {}
            for a in course_activities:
                by_cat.setdefault(a.category, []).append(a)


            for name, cat_activities in sorted(by_cat.iteritems()):
                cat_activities = list(cat_activities)
                hours = sum(activity.duration*activity.tarrif for activity in cat_activities)
                dur = sum(a.duration for a in cat_activities)
                rows.append(({}, 
                    (u'<td></td>'
                    '<td style="font-size: 80%; padding-left: 10%;">{}</td>'
                    '<td>{}</td>'
                    '<td>{}</td>'
                    ).format(name, dur, hours)))

    return rows

@view_config(context=Staff, renderer='templates/staff.pt')
def staff_view(staff, request):

    rows = build_staff_view(staff.activities)
    tbc_staff = staff.tbc

    tbc_activities = []
    for s in tbc_staff:
        tbc_activities.extend(s.activities)

    tbc_rows = build_staff_view(tbc_activities) if tbc_activities else []
    return {'s': staff, 'rows': rows, 'tbc_rows': tbc_rows}

@view_config(context=Divisions, renderer='templates/divisions.pt')
def divisions_view(divisions, request):
    return {'divisions': sorted(zip(*DBSession.query(distinct(Staff.division)).all())[0])}

@view_config(context=Division, renderer='templates/division.pt')
def division_view(division, request):
    return {
    "name": division.name, 
    "staff":
        DBSession
        .query(Staff)
        .filter(Staff.division == division.name)
        .order_by(Staff.name)
        .all()
    }
