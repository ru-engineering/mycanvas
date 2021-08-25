#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Tool to work with Peerwise participation information and put the grades into CANVAS
Developed by Joseph T. Foley <foley at RU dot IS> as part of the canvas-tools project
Started 2021-08-25
Project home https://github.com/ru-engineering/mycanvas

Debian prerequisites:  canvasapi
  pip install canvasapi
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
    description='Peerwise grading tool')
PARSER.add_argument('--version', action="version", version="%(prog)s 0.1")  #version init was depricated
PARSER.add_argument('course',#required!
                    help='Which course to connect with')
PARSER.add_argument('-c', '--configfile',
                    help='configuration file location (override)')
PARSER.add_argument('-s', '--site', default="production",
                    help='Site to interact with:  test, beta, or production(default)')
PARSER.add_argument('-Q', '--questions', default="5",
                    help='How many questions are required?  (default: 5)')
PARSER.add_argument('-A', '--answers', default="10",
                    help='How many questions are required?  (default: 10)')
PARSER.add_argument('-a', '--assignmentid',
                    help='What is the assignment ID? (Look at URL in CANVAS)')
PARSER.add_argument('--calculator',
                    help='')



ARGS = PARSER.parse_args()
MC = mycanvas.MyCanvas(args=ARGS)

mylog = logging.getLogger("app")
floglevel = logging.DEBUG
cloglevel = logging.INFO
mylog.setLevel(floglevel)
outfilename = MC.course.course_code+"-studentservices.log"

mylog.addHandler(logging.FileHandler(outfilename))
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(cloglevel)
mylog.addHandler(console_handler)
mylog.info("Writing output to %s" % outfilename)
#mylog.debug("File logging set at %s", floglevel)
#mylog.debug("Console logging level at %s", cloglevel)

users = MC.course.get_users(enrollment_type=['student'])

for user in users:
    print(user.login_id)
    # use dir(user) to find the field names
