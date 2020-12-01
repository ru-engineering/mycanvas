#!/usr/bin/python
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Participation evalution for Intro to Engineering Courses in Science and Engineering
T-102-VERK and AT TAEK1002
Developed by Joseph T. Foley <foley at RU dot IS> as part of the canvas-tools project
Started 2018-12-07
Project home https://project.cs.ru.is/projects/canvas-tools
"""
import os
import os.path
import argparse
import sys
import math
import logging
import datetime
import dateutil.parser
import dateutil.tz
import mycanvas

# http://stackoverflow.com/questions/8299270/ultimate-answer-to-relative-python-imports
# relative imports do not work when we run this module directly
PACK_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))
ADDTOPATH = os.path.normpath(os.path.join(PACK_DIR, '..'))
# add more .. depending upon levels deep
sys.path.append(ADDTOPATH)

SCRIPTPATH = os.path.dirname(os.path.realpath(__file__))
DEVNULL = open(os.devnull, 'wb')


### Parsing our arguments
PARSER = argparse.ArgumentParser(
    description='Library for working with CANVAS REST API V.1')
PARSER.add_argument('--version', action="version", version="%(prog)s 0.1")  #version init was depricated
PARSER.add_argument('course',#required!
                    help='Which course to connect with')
PARSER.add_argument('-f', '--configfile',
                    help='configuration file location (override)')
PARSER.add_argument('-s', '--site', default="production",
                    help='Which site to interact with:  test or production')
PARSER.add_argument('-p', '--passing', default=0.75, type=float,
                    help='Passing threshold (0-1), default 0.75')

ARGS = PARSER.parse_args()

MC = mycanvas.MyCanvas(args=ARGS)

today_datetime = datetime.datetime.now(dateutil.tz.tzutc()) # We need to see how many have already passed
#outfilename = MC.course.course_code+"-participation"+today_datetime.isoformat()+".txt"
outfilename = MC.course.course_code+"-participation.txt"
try:
    os.remove(outfilename)
except Exception:
    pass# probably doens't exist
mylog = logging.getLogger("app")
floglevel = logging.DEBUG
cloglevel = logging.INFO
mylog.setLevel(floglevel)
mylog.addHandler(logging.FileHandler(outfilename))
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(cloglevel)
mylog.addHandler(console_handler)
mylog.info("Writing output to %s" % outfilename)
#mylog.debug("File logging set at %s", floglevel)
#mylog.debug("Console logging level at %s", cloglevel)

point_accum = { }
for student in MC.students:
    sid = student.id
    point_accum[sid] = 0

### ARGH!  The AssignmentGroup has some sort of bug where it does not include the assignment ids!
### So we can't use it
mylog.info("Report for %s", today_datetime)

## We assume that each attendance is 1 point
score_max = 0
today_max = 0
assignments = MC.find_assignments("Attend")
#for assignment in assignments:
for assignment in assignments:#testing
    mylog.info(assignment)
    due_at_str = assignment.due_at
    due_at = dateutil.parser.parse(due_at_str)
    if today_datetime > due_at:
        mylog.info("(%s) is CLOSED!", due_at)
        today_max += 1#WARNING!  Assuming 1 point per
    else:
        mylog.info("(%s) is Still open",due_at)
   
    score_max += 1
    for submission in assignment.get_submissions():
        score = submission.score
        if score:
            point_accum[submission.user_id] += submission.score
mylog.info("The maximum at the close of the course is %d", score_max)
mylog.info("Today's max is %d.",today_max)
# Figure out passing for whole class
score_min = math.floor(ARGS.passing * score_max)
mylog.info("Minimum passing for complete class is %d.", score_min)
allowed_miss = score_max - score_min
mylog.info("Allowed missing points is %d", allowed_miss)
today_min = today_max - allowed_miss
mylog.info("Minimum passing score today is %d", today_min)

## Now to match names to grades
for student in MC.students:
    points = point_accum[student.id]
    verdict = "pass"
    status = ""
    if points < today_min:
        verdict = "*FAIL*!"
        status = "!!!"
    outstr = "%s%s: %s -> %s" % (status,student, points, verdict)
    mylog.info(outstr)
