# -*- coding:utf-8 -*- 
# --------------------
# Author:
# Description:
# --------------------
import time
import datetime
from handlers import BaseADHandler
from tornado.concurrent import Future
from tornado.gen import coroutine, Return
from core import Session


class BaseWSHandler(BaseADHandler):
    """
    Base handler class for WebServices.
    Other handler in WebServices must inherit from this class.
    """


    @staticmethod
    def get_expiration(timestamp):
        """
        @param: timestamp = 1494558345
        """
        t = time.localtime(timestamp)
        status = True if timestamp < time.time() else False
        return status, time.strftime('%Y-%m-%d %H:%M:%S', t)

    @staticmethod
    def get_buy_start_end_time(duration_value, duration_type):
        """
        @param: duration_value: int  购买时长
        @param: duration_type: string 购买时长类型: '1'-年 | '2'-月 | '3'-日 | '4'-小时
        Calculate order start and end time
        """
        # TODO use timedelta
        start = int(time.time())
        duration_type = str(duration_type)
        end = ''
        if duration_type == '1':
            end = start + duration_value * 365 * 24 * 3600
        elif duration_type == '2':
            end = start + duration_value * 30 * 24 * 3600
        elif duration_type == '3':
            end = start + duration_value * 24 * 3600
        elif duration_type == '4':
            end = start + duration_value * 3600
        else:
            raise ValueError('duration value error. {0}'.format("'1'-年 | '2'-月 | '3'-日 | '4'-小时"))
        return start, end

    def is_balance_enough(self, order_price):
        """检查用户余额是否足够支付当前订单"""
        # XXX: check after user recharge success, user info in session is updated?
        if self.user_info['money'] - order_price >= 0:
            return True
        else:
            return False

    @staticmethod
    def check_result(res, msg='http request error.'):
        if res.get('code') != 1:
            raise Exception(res.get('msg', msg))
