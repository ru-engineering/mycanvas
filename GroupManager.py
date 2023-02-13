#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long,star-args 
# pychecker: disable=line-too-long disable=star-args
"""Tool to work with group/section information from CANVAS
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
import sqlite3

import mycanvas


# http://stackoverflow.com/questions/8299270/ultimate-answer-to-relative-python-imports
# relative imports do not work when we run this module directly
PACK_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))
ADDTOPATH = os.path.normpath(os.path.join(PACK_DIR, '..'))
# add more .. depending upon levels deep
sys.path.append(ADDTOPATH)

SCRIPTPATH = os.path.dirname(os.path.realpath(__file__))
DEVNULL = open(os.devnull, 'wb')

class GroupManager(object):
    """DB interface for CANVAS objects that get catched"""
    def __init__(self, args):
        "setup:  expect a logger and the command line args that are relevant"
        self.dbcon = sqlite3.connect(args.dbfile)
        self.mycanvas = mycanvas.MyCanvas(args=args)
        self.args = args
        
        # set up logging
        mylog = logging.getLogger("groupmanager")
        floglevel = logging.DEBUG
        cloglevel = logging.INFO
        mylog.setLevel(floglevel)
        outfilename = self.mycanvas.course.course_code+"-groupmanager.log"
    
        mylog.addHandler(logging.FileHandler(outfilename))
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(cloglevel)
        mylog.addHandler(console_handler)
        mylog.info("Writing output to %s" % outfilename)
        #mylog.debug("File logging set at %s", floglevel)
        #mylog.debug("Console logging level at %s", cloglevel)
        self.mylog = mylog
        
    def load_from_net(self):
        """Grab CANVAS data for our cache DB"""
        cur = self.dbcon.cursor()
        mc = self.mycanvas
        mylog = self.mylog
        "Load a DB from CANVAS data"
        # first we build a section database
        # https://canvas.instructure.com/doc/api/sections.htlm
        cur.execute("DROP TABLE IF EXISTS sections")
        cur.execute("CREATE TABLE sections(id, name)")
        self.dbcon.commit()
        sections = mc.course.get_sections(include=['total_students'])
        ## total_students can be used to ignore the un-used sections
        for section in sections:
            record = (section.id,section.name)
            cur.execute("INSERT INTO sections VALUES(?, ?)", record)            
            mylog.info(f"section: {record}")            
        self.dbcon.commit()

        cur.execute("DROP TABLE IF EXISTS enrollments")
        cur.execute("CREATE TABLE enrollments(id, section, user_id, user_sortable_name, group_id )")    
        # Get the enrollements and start building main database
        # https://canvas.instructure.com/doc/api/enrollments.html
        enrollments = mc.course.get_enrollments(role=['StudentEnrollment'])
        ## not sure what to do with Prófa nemanda (EN: test user)
        for enrollment in enrollments:
            # each enrollment has a user field
            # in some ways this is like a meta-user
            user = enrollment.user
            section_id = enrollment.course_section_id
            record = (enrollment.id, section_id, user['id'],user['sortable_name'],0)
            # 0 is placeholder for group later
            cur.execute("INSERT INTO enrollments VALUES(?,?,?,?,?)",record)            
            mylog.info(f"enrollment {record}")
        self.dbcon.commit()

        # now group database
        # https://canvas.instructure.com/doc/api/groups.html#method.groups.context_index
        cur.execute("DROP TABLE IF EXISTS groups")
        cur.execute("CREATE TABLE groups(id, name)")
        groups = mc.course.get_groups(include=['users'])
        for group in groups:
            record = (group.id,group.name)
            cur.execute("INSERT INTO groups VALUES(?,?)",record)
            mylog.info(f"group {record}")
            # now we need to put an entry on the enrollment for each user
            for user in group.users:
                #print(user)
                cur.execute("UPDATE enrollments SET group_id = ? WHERE user_id = ?;", (group.id, user['id']))
        self.dbcon.commit()
    
        # we also need the user database for the login_id
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("CREATE TABLE users(id, login_id, name)")    
        # https://canvas.instructure.com/doc/api/userss.html
        users = mc.course.get_users(enrollment_type=['student'])
        for user in users:
            record = (user.id, user.login_id, user.name)
            cur.execute("INSERT INTO users VALUES(?,?,?)",record)            
            mylog.info(f"user {record}")
        self.dbcon.commit()
        

            
    def dump(self):
        "Dump out the database nicely"
        cur = self.dbcon.cursor()
        for row in cur.execute("""
        SELECT users.login_id, user_sortable_name, 
        sections.name, groups.name FROM enrollments
        INNER JOIN users
        ON users.id = enrollments.user_id
        INNER JOIN sections 
        ON sections.id = enrollments.section
        INNER JOIN groups
        ON groups.id = enrollments.group_id
        """):
            print(row)

if __name__ == "__main__":
    ### Parsing our arguments
    PARSER = argparse.ArgumentParser(
        description='CANVAS Group Manager tool')
    PARSER.add_argument('--version', action="version", version="%(prog)s 0.1")  #version init was depricated
    PARSER.add_argument('course',#required!
                        help='Which course to connect with')
    PARSER.add_argument('action',#required!
                        help='what to do?')
    PARSER.add_argument('-c', '--configfile',
                        help='configuration file location (override)')
    PARSER.add_argument('-s', '--site', default="production",
                        help='Site to interact with:  test, beta, or production(default)')
    PARSER.add_argument('-f', '--dbfile', default="groupmanager.db",
                        help='group caching database')
    
    ARGS = PARSER.parse_args()

    GM = GroupManager(ARGS)    
    if ARGS.action == "load":
        GM.load_from_net()
    elif ARGS.action == "dump":
        # dump to screen by default
        GM.dump()
    

#if ARGS.dumpfields:
#    print(dir(users[0]))
#    sys.exit(0)
#print(sections[0].name)
#for enrolled in enrollements:
#    print(enrolled)
    # print(getattr(user, ARGS.fields)) to get the fields
    # use dir(user) to find the field names
