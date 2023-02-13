#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Tool to dump group information from CANVAS
Developed by Joseph T. Foley <foley at RU dot IS>
Started 2023-02-13
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
    description='Library for working with CANVAS REST API V.1')
PARSER.add_argument('--version', action="version", version="%(prog)s 0.1")  #version init was depricated
PARSER.add_argument('course',#required!
                    help='Which course to connect with')
PARSER.add_argument('-c', '--configfile',
                    help='configuration file location (override)')
PARSER.add_argument('-s', '--site', default="production",
                    help='Site to interact with:  test, beta, or production(default)')
PARSER.add_argument('-F', '--fields', default="login_id",
                    help='What student information to extact')
PARSER.add_argument('--dumpfields', action="store_true",
                    help='Dump all the fields')


ARGS = PARSER.parse_args()
MC = mycanvas.MyCanvas(args=ARGS)

mylog = logging.getLogger("app")
floglevel = logging.DEBUG
cloglevel = logging.INFO
mylog.setLevel(floglevel)
outfilename = MC.course.course_code+"-groupmanagement.log"

mylog.addHandler(logging.FileHandler(outfilename))
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(cloglevel)
mylog.addHandler(console_handler)
mylog.info("Writing output to %s" % outfilename)
#mylog.debug("File logging set at %s", floglevel)
#mylog.debug("Console logging level at %s", cloglevel)


# first we build a section database
# https://canvas.instructure.com/doc/api/sections.htlm
sections = MC.course.get_sections()
SECTIONDB = {}
for section in sections:
    (id, name) = (section.id,section.name)
    mylog.info(f"section {id}:{name}")
    SECTIONDB[id]=name

# now group database
# https://canvas.instructure.com/doc/api/groups.html#method.groups.context_index
groups = MC.course.get_groups(include=['users'])
GROUPDB = {}
for group in groups:
    (id, name) = (group.id,group.name)
    mylog.info(f"group {id}:{name}")
    GROUPDB[id]=name

# now go through the enrollments checking the section
# https://canvas.instructure.com/doc/api/enrollments.html
enrollments = MC.course.get_enrollments()

#if ARGS.dumpfields:
#    print(dir(users[0]))
#    sys.exit(0)
#print(sections[0].name)
#for enrolled in enrollements:
#    print(enrolled)
    # print(getattr(user, ARGS.fields)) to get the fields
    # use dir(user) to find the field names
