#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""


import re
import io
import csv
import sqlite3
import itertools
from pathlib import Path
from shutil import copyfile
from bottle import response, route, run
from bottle import jinja2_template as template

__appname__ = "AmoebaServer"
__author__ = "Antoni Kaniowski"
__version__ = "0.1"
__license__ = "wtfpl"

# Store number of rows just to handle properly
no_cols = None
# Check if file exists, if not, bootstrap it from the sample
db_file = Path("db.sqlite")
if not db_file.is_file():
    copyfile("db.sqlite.sample", "db.sqlite")

db = sqlite3.connect("db.sqlite")


# Renders the table
@route('/')
def print_items():
    cursor = db.execute('SELECT * FROM t1')
    # FIXME handle no database case with grace
    # FIXME Set number of rows to be x
    return template('table.html',
                    headings=list(map(lambda x: x[0], cursor.description)),
                    items=cursor.fetchall())


# Sends the sqlite file
@route('/download')
def get_sqlite():
    response.headers['Content-Disposition'] = \
        'attachment; filename="database.sqlite"'
    buffer = io.StringIO()
    for line in db.iterdump():
        buffer.write('%s\n' % line)

    return buffer.getvalue()


# Sends the csv of the db
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
    # --
    return template('<pre>{{o}}</pre>', o=output.getvalue())


# Create groups from data
def grouper(n, iterable, fillVal=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(fillvalue=fillVal, *args)


# Insert bulk rows
def binsert(rows):
    reg = re.compile('(?:[^,(]|\([^)]*\))*')
    data = [item.rstrip(")").lstrip("(").split(", ")
            for item in reg.findall(rows)]
    dta = [tuple(item) for item in data if len(item) > 1]
    # TODO Fix the import so that it is quite fast
    # --
    try:
        # TODO FIXME execute many for multiple values for multiple columns
        db.executemany("INSERT INTO t1 VALUES (?, ?)", dta)
        db.commit()
    except:
        # TODO Try to catch the exception
        raise
    return "Successfully inserted %s" % rows


def get_first():
    cursor = db.execute("SELECT * FROM t1 LIMIT 1")
    return cursor.fetchall()


@route('/insert/<rows>')
def insert(rows):
    # TODO Fix both imports to reuse parts so that bulk and simple are same
    global no_cols
    if no_cols is None:
        no_cols = len(get_first()[0])
    # --
    rd = csv.DictReader(io.StringIO(rows))
    # --
    dta = [item.rstrip(")").lstrip(" (") for item in rd.fieldnames]
    data = list(grouper(no_cols, dta))
    # --
    fields = ("?, " * no_cols).rstrip(", ")
    command = "INSERT INTO t1 VALUES (%s)" % fields
    # --
    db.executemany(command, data)
    db.commit()
    return "Successfully inserted %s" % rows
#    if rows.startswith("("):
#        binsert(rows)
#        return binsert(rows)
#    else:
#        reader_list = csv.DictReader(io.StringIO(rows))
#        header = reader_list.fieldnames
#        h = ",".join("\'"+str(x)+"\'" for x in header)
#        statement = 'INSERT INTO t1 VALUES({h})'.format(h=h)
#        db.execute(statement)
#        db.commit()
#        return "Successfully inserted: \r" + statement


# Creates a new table
@route('/init/<rows>')
def init(rows):
    global no_cols
    reader_list = csv.DictReader(io.StringIO(rows))
    header = reader_list.fieldnames
    no_cols = len(header)
    try:
        h = " varchar, ".join(str(x) for x in header)
        statement = 'CREATE TABLE t1 ({h} varchar)'.format(h=h)
        print(statement)
        db.execute('DROP TABLE IF EXISTS t1')
        db.execute(statement)
        db.commit()
    except sqlite3.OperationalError:
        # TODO Try to switch keywords with non-keywords
        print("Check your init statement. Keywords are not allowed.")
        raise

    return "Ran: \r" + statement

run(host='0.0.0.0', port=8888)
