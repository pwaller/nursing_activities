import os
import sys
import transaction

from datetime import datetime, timedelta

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Base,
    Activity,
    Semester,
    ActivityItem,
    Staff,
    Programme,
    Course,
    Cohort,
    Topic,
    )

import xlrd, xlrd.xldate
from xlrd import open_workbook, xldate_as_tuple, XL_CELL_DATE


def import_activities(filename):
    workbook = open_workbook(filename)

    sheet = workbook.sheet_by_name("Detailed timetable")

    rows = [[c.value for c in sheet.row(i)] for i in xrange(sheet.nrows)]

    columns = rows.pop(0)

    assert columns == [u'Activity', u'Programme ', u'Cohort', u'CS Code',
        u"Unit tilte / Role", u'Date', u'Semester', u'Day of week', u'Time',
        u'AM/PM', u'Topic', u'Category', u'Duration', u'Groups', u'Staff',
        u'Tarrif', u'Total time', '', '', ''], (
            "Columns have changed")

    for row in rows:
        
        (activity, programme, cohort, cs_code, unit_title, date, semester, dow,
            time, tod, topic, category, duration, groups, staff, tarrif, _, _, _, _) = row

        activity = Activity.get(activity)

        programme = Programme.get(programme)
        cohort = Cohort.get(cohort, programme=programme)

        course = Course.get(unit_title, cs_code=cs_code)
        semester = Semester.get(semester)
        staff = Staff.get(staff)

        if topic:
            topic = Topic.get(topic)
        else:
            topic = None

        item = ActivityItem()

        if date and isinstance(date, float):
            date = datetime(*xldate_as_tuple(date, workbook.datemode))
            item.time = date
            if time and isinstance(time, float):
                try:
                    _, _, _, h, m, s = xldate_as_tuple(time, workbook.datemode)
                    item.time += timedelta(seconds=s + 60*(m + 60*h))
                except xlrd.xldate.XLDateAmbiguous:
                    # TODO: Warn about this
                    pass
            else:
                # TODO: Something with this
                pass
        else:
            # TODO: Warn about this happening
            pass

        item.activity = activity
        item.staff = staff
        item.course = course
        item.duration = duration if duration else 0
        item.tarrif = tarrif if tarrif else 0

        item.topic = topic
        item.category = category
        
def import_staff_data(filename):
    workbook = open_workbook(filename)

    sheet = workbook.sheet_by_name("Sheet1")

    rows = [[c.value for c in sheet.row(i)] for i in xrange(sheet.nrows)]

    columns = rows.pop(0)

    assert columns == [u'Full name', u'Surname', u'Foreman', u'Role',
        u'Divison', u'Contract type', u'Full time'], (
            "Columns have changed: {0}".format(columns))

    print "Will import", len(rows), "rows"
    def tryfloat(f):
        try:
            return float(f)
        except ValueError:
            return 0

    for row in rows:
        name, _, _, _, division, contract_type, full_time_equivalent = row

        s = Staff.get(name)
        s.division = division
        s.contract_type = contract_type

        s.full_time_equivalent = tryfloat(full_time_equivalent)


    """
    (staff_names,) = zip(*DBSession.query(Staff.name).all())

    from difflib import get_close_matches
    for name in staff_names:
        if "confirmed" in name.lower() or "external" in name.lower():
            continue

        closest = [n for n in get_close_matches(name, staff_names, cutoff=0.75) if n != name]
        if closest:
            print name, " - ", closest
            """

        #Staff.get(name)
        

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)

    settings = get_appsettings(config_uri)

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    with transaction.manager:
        import_activities("Master timetable.xlsx")
        import_staff_data("Staff list.xls")
