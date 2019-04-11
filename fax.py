#!/usr/bin/env python
"""Poor Man's Email to Fax Gateway.

This is a proof of concept email to fax gateway.  There are multiple aspects
that would have to be improved for it to be used in a production environment.

Copyright (C) 2010 - Russell Bryant, Leif Madsen, Jim Van Meggelen
Asterisk: The Definitive Guide
"""

import sys
import os
import email
import base64
import shutil
import socket


AMI_HOST = "localhost"
AMI_PORT = 5038
AMI_USER = "hello"
AMI_PASS = "world"

# This script will pull a TIFF out of an email and save it off to disk to allow
# the SendFax() application in Asterisk to send it.  This is the location on
# disk where the TIFF will be stored.
TIFF_LOCATION = "/tmp/loremipsum.tif"


# Read an email from stdin and parse it.
msg = email.message_from_file(sys.stdin)

# For testing purposes, if you wanted to read an email from a file, you could
# do this, instead.
#try:
#    f = open("email.txt", "r")
#    msg = email.message_from_file(f)
#    f.close()
#except IOError:
#    print "Failed to open email input file."
#    sys.exit(1)

# This next part pulls out a TIFF file attachment from the email and saves it
# off to disk in a format that can be used by the SendFax() application.  This
# part of the script is incredibly non-flexible.  It assumes that the TIFF file
# will be in a specific location in the structure of the message (the second
# part of the payload, after the main body).  Further, it assumes that the
# encoding of the TIFF attachment is base64.  This was the case for the test
# email that we were using that we generated with mutt.  Emails sent by users'
# desktop email clients will vary in _many_ ways.  To be used with user-
# generated emails, this section would have to be much more flexible.
try:
    f2 = open(TIFF_LOCATION, "w")
    f2.write(base64.b64decode(msg.get_payload()[1].get_payload().replace("\n", "")))
    f2.close()
except IOError:
    print "Failed to open file for saving off TIFF attachment."
    sys.exit(1)

# Now that we have a TIFF file to fax, connect to the Asterisk Manager Interface
# to originate a call.
ami_commands = """Action: Login\r
Username: %s\r
Secret: %s\r
\r
Action: Originate\r
Channel: Local/s@sendfax/n\r
Context: receivefax\r
Extension: s\r
Priority: 1\r
SetVar: SUBJECT=%s\r
\r
Action: Logoff\r
\r
""" % (AMI_USER, AMI_PASS, msg['subject'])

print ami_commands

def my_send(s, data):
    """Ensure that we send out the whole data buffer.
    """
    sent = 0
    while sent < len(data):
        res = s.send(data[sent:])
        if res == 0:
            break
        sent = sent + res

def my_recv(s):
    """Read input until there is nothing else to read.
    """
    while True:
        res = s.recv(4096)
        if len(res) == 0:
            break
        print res

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((AMI_HOST, AMI_PORT))
my_send(s, ami_commands)
my_recv(s)
s.shutdown(socket.SHUT_RDWR)
s.close()
