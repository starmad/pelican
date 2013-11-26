#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi

import cgitb
cgitb.enable()

import sys

form = cgi.FieldStorage()


if not ( form.has_key("slug")
    and  form.has_key("lang")
    and  form.has_key("realname")
    and  form.has_key("email")
    and  form.has_key("comment")
   ):
    print 'Location: /pages/comment-error.html'
    print

    sys.exit(0)

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email import Charset
from email.Utils import formataddr
from subprocess import Popen, PIPE
from hashlib import md5


slug = form.getvalue('slug').decode('utf8')
lang = form.getvalue('lang').decode('utf8')
realname = form.getvalue('realname').decode('utf8')
email = form.getvalue('email').decode('utf8')
website = form.getvalue('website','').decode('utf8')
website = website.strip()
# [TODO] handle https
if website == u"http://":
    website = u""
if not website.startswith(u"http://"):
    website = u"http://" + website
comment = form.getvalue('comment').decode('utf8')

id_ =  md5(comment.encode('utf8')).hexdigest()

content = u"""slug: %(slug)s
lang: %(lang)s
author: %(realname)s
email: %(email)s
website: %(website)s
id: %(id)s
----------
%(comment)s
""" % {'slug':slug, 'lang':lang, 'realname':realname, 'email':email, 'website':website, 'id':id_, 'comment':comment}
content = content.encode('utf8')

subject = u"[Comment] %(slug)s - %(name)s" % {'slug': slug, 'name' : realname}

send_name = str(Header(realname, "utf8"))
email = str(Header(email, "utf8"))


To=u"comment-box@hostname.example"
msg = MIMEText(content, "plain", "utf8")
msg["From"] = formataddr((realname, email))
msg["To"] = Header(To, 'utf8')
msg.add_header('reply-to', str(Header(To, 'utf8')))

msg["Subject"] =  Header(subject, 'utf8')

p = Popen(["/usr/lib/sendmail", "-t"], stdin=PIPE)
p.communicate(msg.as_string())

print 'Location: /pages/comment-ok.html'
print
