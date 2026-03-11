#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Tool to look at submitted files and apply a heuristic
For now, we have hardcoded PDF checking: modularize later
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
from pathlib import PurePath
import tempfile
from decimal import Decimal
import decimal
from PyPDF2 import PdfReader
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
PARSER.add_argument('--kbmax', default="200",
                    help="Max page size in KB")
PARSER.add_argument('--kbthresh', default="2000",
                    help="Files below this threshold accepted regardless of pagecount")
PARSER.add_argument('--penalty', default="5",
                    help="Penalty for oversize")

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

def pdfpagecount(inpath):
    with open(inpath, mode="rb") as infd:
        #pdfdoc = PdfFileReader(infd)
        pdfdoc = PdfReader(infd)
        totalpages = len(pdfdoc.pages)
        #print(f"{inpath} has {totalpages} pages.")
        return totalpages
decimal.getcontext().prec=5

## help from https://siever.info/canvas/GetAllComments.py
#for user in users:
#    print(f"{user.login_id}({user.id})")
#    sub = assignment.get_submission(user.id, include=['submission_comments'])
#    for c in sub.submission_comments:
#        print(c['comment'])
for user in users:
    print(f"{user.login_id}({user.id})")
    sub = assignment.get_submission(user.id, include=['submission_comments'])
    ## Hmm.  Slight problem:  my comments don't show up as submission_comments
    sub_methods = [method_name for method_name in dir(sub)
                  if callable(getattr(sub, method_name))]
    sub_attributes = vars(sub)
    mylog.debug(sub_methods)
    mylog.debug(sub_attributes)
    
    if len(sub.attachments) == 0:
        print("no files")
        continue
    # TODO:  check if this already has feedback    
    
    thefile = sub.attachments[-1]
    filepath = f"a{sub.assignment_id}_u{sub.user_id}_{thefile}"
    realfile = thefile
    print(f"Downloading for {user}: {filepath}")
    thefile.download(filepath)
    count = pdfpagecount(filepath)
    maxsizekb = Decimal(count)*200
    size = Decimal(os.path.getsize(filepath))
    sizekb = size/Decimal(1024)
    sizemb = sizekb/Decimal(1024)
    os.unlink(filepath)#cleanup
    judgementstr = "File meets size requirements. Well done."#assume met the size requirement
    if sizekb > maxsizekb:
        if sizekb <= Decimal(ARGS.kbthresh):
            judgementstr = "File is under 2000KB threshold."
        else:
            judgementstr = "File does not meet size requirement on assignment (-5%)."
    commentstr = f"FILECHECK:{realfile} has {count} pages so max allowed size is {maxsizekb}KB.\nSubmitted file size is {sizekb}KB. {judgementstr}"
    mylog.info(f"student: {user.login_id} comment: {commentstr}")
    ##Inspired by https://github.com/wwong2025/canvas_comments_upload/blob/main/canvas_comments_upload.py
    ## TODO:  make idempotent if I can check the existing comments
    ## So far, I can only look at student comments
    sub.edit(comment={"text_comment":commentstr})
    break##DEBUG
