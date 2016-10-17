#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__appname__ = "AmoebaServer"
__author__  = "Antoni Kaniowski"
__version__ = "0.1"
__license__ = "wtfpl"

import logging, sqlite3, csv, io
from bottle import static_file, response,route, run, route, jinja2_template as template
from io import StringIO
from pathlib import Path
from shutil import copyfile


# Check if file exists, if not, bootstrap it from the sample
db_file = Path("db.sqlite")
if not db_file.is_file():
    copyfile("db.sqlite.sample", "db.sqlite")

db = sqlite3.connect("db.sqlite")

#Renders the table
@route('/')
def print_items():
    cursor = db.execute('SELECT * FROM t1')
    # FIXME handle no database case with grace
    return template('table.html',
            headings = list(map(lambda x: x[0], cursor.description)),
            items=cursor.fetchall())

#Sends the sqlite file
@route('/download')
def get_sqlite():
    response.headers['Content-Disposition'] = 'attachment; filename="database.sqlite"'
    buffer = StringIO()
    for line in db.iterdump():
        buffer.write('%s\n' % line)

    return buffer.getvalue()


#Sends the csv of the db
@route('/csv')
def get_csv():
    cursor = db.execute('SELECT * FROM t1')
    header = list(map(lambda x: x[0], cursor.description))
    csvdata = cursor.fetchall()
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    for line in csvdata:
        writer.writerow(line)

    return template('<pre>{{o}}</pre>', o = output.getvalue())

#Creates a new table
@route('/insert/<rows>')
def insert(rows):
    reader_list = csv.DictReader(io.StringIO(rows))
    header = reader_list.fieldnames
    h = ",".join("\'"+str(x)+"\'" for x in header);
    statement = 'INSERT INTO t1 VALUES({h})'.format(h=h)
    print(statement)

    db.execute(statement)
    db.commit()

    return "Ran: \r" + statement

# Creates a new table
@route('/init/<rows>')
def init(rows):
    reader_list = csv.DictReader(io.StringIO(rows))
    header = reader_list.fieldnames
    h = " varchar, ".join(str(x) for x in header)
    statement = 'CREATE TABLE t1 ({h} varchar)'.format(h=h)
    print(statement)

    try:
        db.execute('DROP TABLE IF EXISTS t1')
        db.execute(statement)
        db.commit()
    except sqlite3.OperationalError as e:
        # TODO catch operational exception for sqlite3
        raise

    return "Ran: \r" + statement

run(host='localhost', port=8888)
