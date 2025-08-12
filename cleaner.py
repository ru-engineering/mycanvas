#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Cleanup tool for deleting template elements before importing content from previous course
Developed by Joseph T. Foley <foley at RU dot IS> as part of the canvas-tools project
Started 2020-06-02
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
PARSER.add_argument('-s', '--site', default="test",
                    help='Site to interact with:  test(default), beta, or production')
PARSER.add_argument('-d', '--elements', default="pages",
                    help='Elements to delete: pages, modules, assignment_groups, template')
PARSER.add_argument('-f', '--noconfirm', action='store_true',
                    help="Don't confirm deletion")

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

def query_yes_no(question, default="yes"):
    #https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    if ARGS.noconfirm:  # Force the changes
        return True
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

if ARGS.elements == "pages" or ARGS.elements == "template":
    mylog.info("Preparing to delete pages")
    for page in MC.course.get_pages():
        mylog.info("Considering page: %s", page)
        if query_yes_no(f"Delete page '{page}'?", default=None):
            mylog.info("Deleting '%s'", page)
            try:
                page.delete()
            except canvasapi.exceptions.BadRequest as err:
                mylog.error("Cannot delete this page: %s", err)
        else:
            mylog.info("Skipping '%s'", page)
        

if ARGS.elements == "modules"  or ARGS.elements == "template":
    mylog.info("Preparing to delete modules")
    for module in MC.course.get_modules():
        mylog.info("Considering module: %s", module)
        if query_yes_no(f"Delete module '{module}'?", default=None):
            mylog.info("Deleting '%s'", module)
            module.delete()
        else:
            mylog.info("Skipping '%s'", module)
       

if ARGS.elements == "assignment_groups"  or ARGS.elements == "template":
    mylog.info("Preparing to delete assignment_groups")
    for assignment_group in MC.course.get_assignment_groups():
        mylog.warning("CANVAS does not allow there to be zero assignment groups, so it will create one if the list is empty.")
        mylog.info("Considering assignment_group: %s", assignment_group)
        if query_yes_no(f"Delete assignment_group '{assignment_group}'?", default=None):
            mylog.info("Deleting '%s'", assignment_group)
            assignment_group.delete()
        else:
            mylog.info("Skipping '%s'", assignment_group)
        
