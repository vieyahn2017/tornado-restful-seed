#  # !/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2014-09-19 15:28:46
# Last modified:2017-05-23 11:13:20
# Filename:urls.py
# Description:
import os

from tornado.web import StaticFileHandler

from core import context
#from handlers.Webservices.conf.config import FILE_UPLOAD_PATH

module = context['module'].split(",")
module = [m.capitalize() for m in module]

handlers = [
    # (r"/(?P<filename>.*\.txt)", StaticHandler),
    # (r".*", PageNotFoundHandler),
    #(r'/(\d{6})/(\d{2})/.*', StaticFileHandler, {'path': FILE_UPLOAD_PATH})
]

# 检查输入的模块是否存在
# supervisor这边检查会出错，暂时注释掉
# filepath = os.path.join(os.path.abspath(os.path.curdir), 'handlers')
# module = filter(lambda x: os.path.exists(os.path.join(filepath, x)), module)

if module:
    from handlers import Route

    __import__("handlers", fromlist=module)
    handlers.extend(Route.urls)
else:
    exit('not found module')
