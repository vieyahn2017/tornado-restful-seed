#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao
# @created:20170413
## Description: main module, all handlers of Webservices' Modules.
## 2017.05.25 rename to cloud.py

import types
import copy
import json
import urllib
import time
import datetime


from tornado.gen import coroutine, Return
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from tornado.log import app_log
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse, HTTPError


from handlers import BaseHandler, Route
from config import API_VERSION, LOCALHOST_PREFIX


from .captcha import VerifyCode




@Route('webservices/verifycode_vie')
class CloudHostHandler(BaseHandler):


    @coroutine
    def get(self):
        """加self.set_header('Content-type', 'image/GIF')这一句可以直接在客户端显示验证码图片，
        不过我们这个接口是返回StingIO的字节流的接口"""
        vc = VerifyCode(fontColor=(100,211, 90))
        vc.randSeed(4)
        app_log.info(vc.code)
        # self.set_header('Content-type', 'image/GIF')
        self.write(vc.save_stream())
        # 网上说的另外一种方法，暂存在这，我没测试
        # response = HttpResponse(mimetype="image/gif")
        # im.save(response, "GIF")
        # return response

@Route('webservices/verifycode_img')
class CloudHostHandler(BaseHandler):
    @coroutine
    def get(self):
        self.write('<img src="{0}/api/{1}/webservices/verifycode_vie"/>'.format(LOCALHOST_PREFIX, API_VERSION))
