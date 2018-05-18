from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import sys
import os
import datetime
import time
import subprocess

mailto_list = ["roy_wang109@163.com"]
mail_host = "smtp.126.com"
mail_user = "munaiyi609@126.com"
mail_pass = "a609330246"



def send_mail(to_list, sub, content):
    me = "LogServer"+"<"+mail_user+">"
    msg = MIMEText(content, _subtype='plain', _charset='utf-8')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user, mail_pass)
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        print "Email sent!"
        return True
    except Exception, e:
        print str(e)
        return False


if __name__ == '__main__':
        send_mail(mailto_list, 'submit', 'content')
