# -*- coding:utf-8 -*- 
# --------------------
# Author:
# Description:	
# --------------------
# TODO 异步外理
import smtplib
from email.mime.text import MIMEText

from tornado.log import app_log


# mail_host = "smtp.163.com"       #使用的邮箱的smtp服务器地址，这里是163的smtp地址
# mail_user = "wz2017python"       #用户名
# mail_pass = "wz2017python"       #密码
# mail_postfix = "163.com"         #邮箱的后缀
# to_list                          #收件人(列表)，以';'分隔
# sub                              # 主题
# content                          # 内容
# subtype
def send_mail(mail_host, mail_user, mail_pass, mail_postfix,
              to_list, sub, content, subtype='plain'):
    me = "MicroCloud" + "<" + mail_user + "@" + mail_postfix + ">"
    msg = MIMEText(content, _subtype=subtype, _charset='utf-8')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)  # 连接服务器
        server.login(mail_user, mail_pass)  # 登录操作
        server.sendmail(me, to_list, msg.as_string())  # 发送
        server.close()
        return True
    except Exception as e:
        app_log.error(e)
        return False
