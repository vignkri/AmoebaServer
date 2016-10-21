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

# Custom tools
import utils

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
    """Print the data in the database in a tabular form"""
    cursor = db.execute('SELECT * FROM t1')
    # FIXME handle no database case with grace
    # FIXME Set number of rows to be x
    return template('table.html',
                    headings=list(map(lambda x: x[0], cursor.description)),
                    items=cursor.fetchall())


# Sends the sqlite file
@route('/download')
def get_sqlite():
    """Get the sqlite file and download it"""
    response.headers['Content-Disposition'] = \
        'attachment; filename="database.sqlite"'
    buffer = io.StringIO()
    for line in db.iterdump():
        buffer.write('%s\n' % line)

    return buffer.getvalue()


# Sends the csv of the db
@route('/csv')
def get_csv():
    """Get the csv file from the database"""
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


def get_one():
    """Get one row of the database"""
    cursor = db.execute("SELECT * FROM t1 LIMIT 1")
    return cursor.fetchall()


@route('/insert/<rows>')
def insert(rows):
    """Insert/Bulk insert values into the table.

    Parameter
    --------
    rows : str
        A long string equal to the number of columns in the database
        setup. Each column value is separated by a comma and or by
        delineating each row with a bracket.
    """
    # TODO Try to handle special characters that are difficult
    global no_cols
    if no_cols is None:
        no_cols = len(get_one()[0])
    rd = csv.DictReader(io.StringIO(rows))
    try:
        # TODO Figure out what errors could occur
        dta = [item.rstrip(")").lstrip(" (") for item in rd.fieldnames]
        data = list(utils.grouper(no_cols, dta))
        fields = ("?, " * no_cols).rstrip(", ")
        command = "INSERT INTO t1 VALUES (%s)" % fields
        db.executemany(command, data)
    except:
        raise
    db.commit()
    return "Successfully inserted %s" % rows


# Creates a new table
@route('/init/<rows>')
def init(rows):
    """Initialize a new table with 'n' columns

    Parameter
    ---------
    rows : string
        The rows indicate the column names of the columns in the table.
        Each of columns are separated by a comma to indicate that they
        are to be takend as the name of the column in the table.
    """
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
