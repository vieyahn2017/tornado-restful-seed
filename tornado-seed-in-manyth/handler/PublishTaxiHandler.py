# -*- coding: utf-8 -*- 
# --------------------
# Author:   yh001 from gxm
# Description:  
# --------------------

from concurrent.futures import ThreadPoolExecutor
from tornado.web import RequestHandler
from tornado.gen import coroutine
from tornado.escape import json_decode

from db.dbManager import rsdb

executor = ThreadPoolExecutor(8)

# 数据推送操作类型
ACTION = {
    "update": "update",
    "insert": "insert",
    "delete": "delete"
}

#########################################
# 开客户端，订阅，命令如下
# redis-cli
# psubscribe lcic_vehicle_real_location
#########################################

class BaseHandler(RequestHandler):
    def initialize(self):
        self.pageAttr = {"title": "", "pageflag": ""}

    def get_current_user(self):
        email = self.get_secure_cookie('user_name')
        if not email:
            return None
        return 'admin' #test
        #return user_model.get_user_by_email(email)


class BaseMessagePublishHandler(BaseHandler):
    """消息推送基类"""
    def post(self):
        pass

    def do_update(self, msg_body):
        pass

    def do_insert(self, msg_body):
        pass

    def do_delete(self, msg_body):
        pass

    def check_xsrf_cookie(self):
        pass


class PublishTaxiWeijieHandler(BaseMessagePublishHandler):
    @coroutine
    def post(self):
        msg_body = self.request.body
        msg_body_dict = json_decode(msg_body)
        action = msg_body_dict["action"]

        if action == ACTION["update"]:
            yield executor.submit(self.do_update, msg_body)
            self.write({"status": 1})

        elif action == ACTION["insert"]:
            yield executor.submit(self.do_insert, msg_body)
            self.write({"status": 1})

        elif action == ACTION["delete"]:
            yield executor.submit(self.do_delete, msg_body)
            self.write({"status": 1})

        else:
            self.write({"status": 0})

    def do_update(self, msg_body):
        rsdb.publish('lcic_vehicle_real_location', msg_body)
        # 后续的sockjs版本
        #LocationRealTimeUpdateHandler.pub_sub(msg_body)

    def do_insert(self, msg_body):
        rsdb.publish('lcic_vehicle_real_location', msg_body)
        # 后续的sockjs版本
        #LocationRealTimeUpdateHandler.pub_sub(msg_body)

    def do_delete(self, msg_body):
        pass