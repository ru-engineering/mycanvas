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
import logging
import os
import os.path
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
#template_assignment_vars = vars(template_assignment)
#print(template_assignment_vars)


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
        #print("response: %s", response_json)
        response_json.update(course_id=self.course_id)
        return Assignment(self._requester, response_json)


# let's try it out
AD = AssignmentDuplicator(template_assignment)
newassignment = AD.duplicate()
print(vars(newassignment))
