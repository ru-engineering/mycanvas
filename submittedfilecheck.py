#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Tool to look at submitted files and apply a heuristic
Developed by Joseph T. Foley <foley at RU dot IS> as part of the canvas-tools project
Started 2026-03-04
Project home https://github.com/ru-engineering/mycanvas

Debian prerequisites:  canvasapi
  pip install canvasapi
It is best to do this in a virtual environment
"""
import os
import os.path
import argparse
import sys
import logging
import canvasapi
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
PARSER.add_argument('assignment',#required!
                    help='Which assignment to look at')
PARSER.add_argument('-c', '--configfile',
                    help='configuration file location (override)')
PARSER.add_argument('-s', '--site', default="beta",
                    help='Site to interact with:  test, beta, or production(default)')

ARGS = PARSER.parse_args()
MC = mycanvas.MyCanvas(args=ARGS)

mylog = logging.getLogger("app")
floglevel = logging.DEBUG
cloglevel = logging.INFO
mylog.setLevel(floglevel)
outfilename = MC.course.course_code+"-submittefilecheck.log"

mylog.addHandler(logging.FileHandler(outfilename))
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(cloglevel)
mylog.addHandler(console_handler)
mylog.info("Writing output to %s" % outfilename)
#mylog.debug("File logging set at %s", floglevel)
#mylog.debug("Console logging level at %s", cloglevel)

users = MC.course.get_users(enrollment_type=['student'])
assignment = MC.course.get_assignment(ARGS.assignment)

# hint for downloading files
# https://github.com/ucfopen/canvasapi/discussions/634

#for user in users:
user = users[0]
print(f"{user.login_id}({user.id})")
sub = assignment.get_submission(user.id)
if len(sub.attachments) > 0:
    thefile = sub.attachments[-1]
    #tempfilename = f"a{sub.assignment_id}_u{sub.user_id}_{thefile}"
    subfile = f"{thefile}"
    print(f"Downloading for {user}: {subfile}")
    thefile.download(subfile)
#print(f"file:{filetoeval}")


#print(assignment)
