#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,star-args
# pychecker: disable=line-too-long disable=star-args
"""Standard library for interfacing with the Reykjavik University CANVAS LMS
Developed by Joseph T. Foley <foley at RU dot IS> as part of the canvas-tools project
Started 2018-12-06
Project home https://project.cs.ru.is/projects/canvas-tools
API keys can be created under 'Approved Integrations' in profile/settings

Install:
apt install python3-pip
pip3 install canvasapi
"""

## Useful links
#https://canvas.instructure.com/courses/785215/pages/getting-started-with-the-api
#https://github.com/ucfopen/canvasapi
#https://canvas.instructure.com/doc/api/file.developer_keys.html

import os
import os.path
# import sys
# import re
import argparse
#import subprocess
import sys
#import pprint
import logging
import configparser #ConfigParser in py2 configparser in py3
# Import the Canvas class
from canvasapi import Canvas

if __name__ == '__main__':
    # http://stackoverflow.com/questions/8299270/ultimate-answer-to-relative-python-imports
    # relative imports do not work when we run this module directly
    PACK_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))
    ADDTOPATH = os.path.normpath(os.path.join(PACK_DIR, '..'))
    # add more .. depending upon levels deep
    sys.path.append(ADDTOPATH)

SCRIPTPATH = os.path.dirname(os.path.realpath(__file__))
DEVNULL = open(os.devnull, 'wb')

class MyCanvas(object):
    """Setup a reasonable environment to work with the CANVAS REST API V.1
    Most importantly, setup the connection with the appropriate authentication
    """
    scriptpath = SCRIPTPATH
    logfd = None
    log = logging.getLogger("mycanvas")

    def __init__(self, args):
        """Find configuration files with the api
        TODO: Figure out mechanism to avoid key storage
        """
        self.args = args
        # setup logger
        logpath = 'mycanvas.log'
        floglevel = logging.DEBUG
        cloglevel = logging.INFO
        self.log.setLevel(floglevel)
        self.log.addHandler(logging.FileHandler(logpath))
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(cloglevel)
        self.log.addHandler(console_handler)
        self.log.info("Logging to %s", logpath)
        self.log.debug("File logging set at %s", floglevel)
        self.log.debug("Console logging level at %s", cloglevel)

        # setup the config file
        configpaths = [args.configfile, "./mycanvas.ini", "~/.mycanvas.ini"]
        cp = configparser.ConfigParser()
        configfile = None
        def checkfile(filepath):
            return os.path.isfile(filepath) and os.access(filepath, os.R_OK)
        for configpath in configpaths:
            self.log.debug("Looking for config file in %s", configpath)
            if configpath is None:
                continue
            configpath = os.path.expanduser(configpath)  #deal with ~
            if not checkfile(configpath):
                continue
            configfile = cp.read([configpath])
            self.log.info("Using configuration file at %s", configpath)
            break

        if configfile is None:
            self.log.error("Error:  Couldn't find a configuration file.")
            sys.exit()

        def config2dict(section):
            """convert a parsed configuration into a dict for storage"""
            config = {setarg: setval for setarg, setval
                  in cp.items(section)}
            for setarg, setval in config.items():
                self.log.debug('setting: %s = %s', setarg, setval)
            return config
        config = {}
        for section in ['api', 'courses']:
            config[section] = config2dict(section)
        self.config = config
        self.configfile = configfile

        # Initialize a new Canvas object
        url = config['api'][args.site]
        self.log.info("Connecting to %s", url)
        self.canvas = Canvas(url, config['api'][args.site+'_key'])

        # Now which course are we going to work on?
        # If it is an integer, try to use it raw
        course_id = self.args.course
        if not course_id.isdigit():
            try:
                course_id = config['courses'][self.args.course]
            except KeyError:
                self.log.error("Error: No course '%s' found in config", self.args.course)
                sys.exit()
        course = self.canvas.get_course(course_id)
        self.log.info("Course '%s(%s)' selected", course.name, course.id)
        self.course = course
        self.students = self.course.get_users(enrollment_type=['student'])
        ## user fields:  id, name, created_at, sortable_name,
        ##     short_name, sis_user_id, integration_id, login_id

        # for student in self.students:
        #     canvas_id = student.id
        self.a_groups = self.course.get_assignment_groups()

    def find_assignments(self, searchstr):
        """Given a searchstring, try to find all the courses that match"""
        self.log.info("Searching for assignments containing '%s'" % searchstr)
        assignments = self.course.get_assignments()
        matched = []
        for assignment in assignments:
            if assignment.name.find(searchstr) != -1:
                matched.append(assignment)
        return(matched)

    def get_assignment_score(self, assignment_id, student_id):
        """Lookup what a student got on something"""
        #for a_group in a_groups:
        #    print a_group
        assignment = self.course.get_assignment(assignment_id, user_id=student_id)
        submission = assignment.get_submission(student_id)
        return(submission.grade)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(
        description='Library for working with CANVAS REST API V.1')
    PARSER.add_argument('--version', action="version", version="%(prog)s 0.1")  #version init was depricated
    PARSER.add_argument('course',#required!
                        help='Which course to connect with')
    PARSER.add_argument('-c', '--configfile',
                        help='configuration file location (override)')
    PARSER.add_argument('-s', '--site', default="test",
                        help='Which site to interact with:  test(default), beta, or production')

    ARGS=PARSER.parse_args()

    MC = MyCanvas(args=ARGS)

    #student_id = MC.students[0].id
    #print MC.get_assignment_score(13838, student_id)


