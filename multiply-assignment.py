#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Tool for making multiple similar assignments from existing ones
Developed by Joseph T. Foley <foley at RU dot IS> as part of the canvas-tools project
Started 2026-06-26
Project home https://github.com/ru-engineering/mycanvas

Debian prerequisites:  canvasapi
  pip install canvasapi
"""
import argparse
import datetime as dt
import logging
import os
import os.path
#import pprint
import re
import sys



import canvasapi
from canvasapi.assignment import Assignment
from canvasapi.util import combine_kwargs

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
    description='Clean useless template files to prepare for import')
PARSER.add_argument('--version', action="version", version="%(prog)s 0.1")  #version init was depricated
PARSER.add_argument('course',#required!
                    help='Which course to connect with')
PARSER.add_argument('assignment',#required!
                    help='Which course to connect with')
PARSER.add_argument('-c', '--configfile',
                    help='configuration file location (override)')
PARSER.add_argument('-s', '--site', default="test",
                    help='Site to interact with:  test(default), beta, or production')
PARSER.add_argument('--frequency', default="weekly",
                    help='How often to repeat')
PARSER.add_argument('-i', '--instances', default=1, type=int,
                    help='How many additional copies do you want?')

ARGS = PARSER.parse_args()
MC = mycanvas.MyCanvas(args=ARGS)

mylog = logging.getLogger("app")
floglevel = logging.DEBUG
cloglevel = logging.INFO
mylog.setLevel(floglevel)
outfilename = MC.course.course_code+"-cleaner.log"

mylog.addHandler(logging.FileHandler(outfilename))
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(cloglevel)
mylog.addHandler(console_handler)
mylog.info("Writing output to %s" % outfilename)
#mylog.debug("File logging set at %s", floglevel)
#mylog.debug("Console logging level at %s", cloglevel)

## The https://github.com/ucfopen/canvasapi is missing the duplication call in the API
# https://developerdocs.instructure.com/services/canvas/resources/assignments#method.assignments_api.duplicate
# We can call it manually then edit the result
# POST /api/v1/courses/:course_id/assignments/:assignment_id/duplicate
template_assignment = MC.course.get_assignment(ARGS.assignment)
#pp = pprint.PrettyPrinter(indent=2, width=80)
#pp.pprint(vars(template_assignment))
#sys.exit(0)
#template_assignment_vars = vars(template_assignment)
#print(template_assignment_vars)
re_namecheck = re.compile(r'(.*)\s*(\d+)\s*$') #name, number
template_name = template_assignment.name
template_name_match = re_namecheck.match(template_name)
template_number = 1
if template_name_match:
    template_name, template_number  = template_name_match.group(1, 2)
    template_number = int(template_number)
#print(f'name: {template_name}, num: {template_number}')



class AssignmentDuplicator(Assignment):
    def __init__(self, assignment):
        (requester, attributes) = assignment._requester, vars(assignment)
        super(AssignmentDuplicator, self).__init__(requester, attributes)

    def duplicate(self):
        """
        Duplicate assignment and return copy.

        :calls: `POST /api/v1/courses/:course_id/assignments/:assignment_id/duplicate \
        <https://developerdocs.instructure.com/services/canvas/resources/assignments#method.assignments_api.duplicate>`_

        :rtype: :class:`canvasapi.assignment.Assignment`
        """
        response = self._requester.request(
            'POST',
            'courses/{}/assignments/{}/duplicate'.format(self.course_id, self.id),
        )
        response_json = response.json()
        response_json.update(course_id=self.course_id)
        return Assignment(self._requester, response_json)


AD = AssignmentDuplicator(template_assignment)


print(f'Duplicating assignment {template_assignment.id}:"{template_assignment.name}" {ARGS.instances} times')
for i in range(ARGS.instances):
    newassignment = AD.duplicate()
    #print(vars(newassignment))
    increment = i + 1
    # Fix the name and position to increment
    newnumber = template_number + increment
    position = template_assignment.position + increment
    # TODO:  figure why it put #10 after #1
    newname = f'{template_name} {newnumber}'

    assignment_settings = {'name': newname,
                           'position': position}

    delta = dt.timedelta(0)
    if ARGS.frequency == "weekly":
        delta = dt.timedelta(weeks=increment)

    # Adjustment to dates
    dstr = template_assignment.unlock_at
    if dstr:
        template_unlock_at = dt.datetime.fromisoformat(dstr)
        new_unlock_at = template_unlock_at + delta
        print(f'unlock: {template_unlock_at} -> {new_unlock_at}')
        assignment_settings['unlock_at'] = new_unlock_at
        
    dstr = template_assignment.due_at
    if dstr:
        template_due_at = dt.datetime.fromisoformat(dstr)
        new_due_at = template_due_at + delta
        print(f'due: {template_due_at} -> {new_due_at}')
        assignment_settings['due_at'] = new_due_at

    dstr = template_assignment.lock_at
    if dstr:
        template_lock_at = dt.datetime.fromisoformat(dstr)
        new_lock_at = template_lock_at + delta
        print(f'lock: {template_lock_at} -> {new_lock_at}')
        assignment_settings['lock_at'] = new_lock_at

    newassignment.edit(assignment=assignment_settings)
    print(f'Created assignment {newname}')

