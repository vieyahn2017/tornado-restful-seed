#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2017-06-06 15:00:37
# Last modified:2017-06-06 15:00:45
# Filename:models.py
# Description:
from __future__ import absolute_import, with_statement

from functools import wraps

from tornado.gen import coroutine, Return
from tornado.log import app_log

from connproxy import StoreContext, StoreCache
from core import SystemStatus

import traceback

def cache(func):
    @wraps(func)
    def _cache(*args, **kwargs):
        if SystemStatus.cache_server_down():
            app_log.error("cache server down, using database query directly")
            return func(*args, **kwargs)

        model = args[0]
        get_cache_func = model.get_all_from_cache
        cache_func = model.cache_all
        if func.__name__ == "paging":
            get_cache_func = model.get_paging_from_cache
            cache_func = model.cache_paging
        elif func.__name__ == "filter_by":
            get_cache_func = model.get_filter_by_from_cache
            cache_func = model.cache_filter_by

        cached_result = get_cache_func(func.__name__, args, kwargs)
        if cached_result:
            return cached_result
        else:
            db_result = func(*args, **kwargs)
            if db_result:
                cache_func(func.__name__, args, kwargs, db_result)
            return db_result

    return _cache


class BaseModel(object):
    """Some Database operation"""
    @coroutine
    def get(self, query, params=None):
        """
        Returns the (singular) row returned by the given query.
        If the query has no results, returns None.  If it has
        more than one result, raises an exception.
        """
        rows = yield self.query(query, params)
        if not rows:
            raise Return(None)
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for Database.get() query")
        else:
            raise Return(rows[0])

    @coroutine
    def query(self, query, params=None):
        """Returns a row list for the given query and parameters."""
        with StoreContext() as store:
            cur = yield store.execute(query, params)
            res = cur.fetchall()
        raise Return(res)


    @coroutine
    def execute(self, sql, param=None):
        with StoreContext() as store:
            try:
                yield store.execute(sql, param)
                flag = True
            except:
                app_log.error("execute sql failed, raw_sql[{0}], details: {1}".format(sql, traceback.format_exc()))
                flag = False
        raise Return(flag)


    @coroutine
    def batch(self, sql, datas):
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                for param in datas:
                    yield ctx.execute(sql, param)
                yield ctx.commit()
                flag = True
            except:
                app_log.error("batch execute sql failed, raw_sql[{0}], details: {1}".format(sql, traceback.format_exc()))
                yield ctx.rollback()
                flag = False
        raise Return(flag)



class BaseADModel(BaseModel):
    """
    # gxm1015
    Base Class for admin modules.
    It contains some reusable method.
    Other model in Admin can inherit from this class.
    """

    def __init__(self):
        super(BaseADModel, self).__init__()


    @coroutine
    def execute_lastrowid(self, query, params=None):
        """
        Executes the given query, returning the lastrowid from the query.
        """
        with StoreContext() as store:
            cur = yield store.execute(query, params)
            res = cur.lastrowid
        raise Return(res)

    @coroutine
    def execute_rowcount(self, query, params=None):
        """Executes the given query, returning the rowcount from the query."""
        with StoreContext() as store:
            cur = yield store.execute(query, params)
            res = cur.rowcount
        raise Return(res)

    @coroutine
    def begin(self):
        """
        Start transaction
        Wait to get connection and returns `Transaction` object.
        :return: Future[Transaction]
        :rtype: Future
        """
        with StoreContext() as store:
            ctx = yield store.begin()
        raise Return(ctx)

    insert = execute_lastrowid
    update = execute_rowcount
    delete = execute_rowcount

    @property
    def cache_server(self):
        with StoreCache() as mc:
            return mc


    @staticmethod
    def filter_param_by_value(param_dict, value=None):
        """9.5 如果是前端传来-1，设置为value"""
        for k, v in param_dict.items():
            if v == -1 or v =='-1':
                param_dict[k] = value

    @staticmethod
    def filter_param_delimiting(param_dict):
        """filter值是-1的项，从js前端传来的默认值. 8.18. 9.5从handler改到model"""
        for k, v in param_dict.items():
            if v == -1 or v =='-1':
                del param_dict[k]

    @classmethod
    def filter_param_delimiting_batch(cls, param_list):
        for param_dict in param_list:
            cls.filter_param_delimiting(param_dict)

    @staticmethod
    def trans_update_sql_param_dict(param_dict):
        """ trans_update_sql_param_dict 2017.9.5 """
        return ",".join(["{0}=%s".format(x) for x in param_dict.keys()])

    @classmethod
    def make_update_sql_by_dict(cls, db, _id, param_dict, id_key='_id'):
        """ make_update_sql_by_dict: 2017.9.5 """
        set_list_str = cls.trans_update_sql_param_dict(param_dict)
        return "UPDATE {0} SET {1} WHERE {2}={3};".format(db, set_list_str, id_key, _id)


    @coroutine
    def update_by_dict(self, db, _id, param_dict, is_log=False):
        """ update 2017.7.26  set_list_str支持可变参数，拼接sql。
        子类的单数据库可以直接引用本方法，多数据库操作要自己写 
        
        2017.9.5 split two methods bellow:
          self.trans_update_sql_param_dict
          self.make_update_sql_by_dict

        todo:
          yield self.execute(sql, tuple(param_dict.values()))
          参数调用采用的：
          tuple(param_dict.values()) 
          不太好，可以参照下面的insert，改成dict映射的方式。


        make_insert_sql_by_dict采用拼接的方式，字段只能少于数据库的字段，不能多于
        考虑todo：增加一个filter_keys的参数 

        """
        sql = self.make_update_sql_by_dict(db, _id, param_dict)
        flag = yield self.execute(sql, tuple(param_dict.values()))
        if is_log:
            app_log.info(("update ?", flag, db, _id, param_dict, "sql=", sql))
        raise Return(flag)


    @staticmethod
    def trans_insert_sql_param_dict(param_dict):
        """ trans_insert_sql_param_dict 2017.9.6 """
        list_keys_str = ",".join(param_dict.keys())
        sfmt_keys_str = ",".join(["%({0})s".format(x) for x in param_dict.keys()])
        return list_keys_str, sfmt_keys_str

    @classmethod
    def make_insert_sql_by_dict(cls, db, param_dict):
        """ make_insert_sql_by_dict: 2017.9.6 

        处理这样的sql语句，封装本方法
        yield ctx.execute('INSERT INTO order_finance_info (order_id, discount, score_deduction, tax, logistics_expense,'
                         ' packing_expense, total_payment, actual_payment, unpaid_total, finance_charge_type_id,'
                         ' finance_charge_status_id, payment_time, finance_verify_status_id, finance_verify_man) '
                         'VALUES (%(order_id)s, %(discount)s, %(score_deduction)s, %(tax)s, %(logistics_expense)s, %(packing_expense)s, %(total_payment)s,'  
                         '%(actual_payment)s, %(unpaid_total)s, %(finance_charge_type_id)s, %(finance_charge_status_id)s, %(payment_time)s, '
                         '%(finance_verify_status_id)s, %(finance_verify_man)s )', order_finance_info_dict
        )
        调用如self.insert_by_dict所示
        """
        list_keys_str, sfmt_keys_str = cls.trans_insert_sql_param_dict(param_dict)
        return "INSERT INTO {0} ({1}) VALUES ({2});".format(db, list_keys_str, sfmt_keys_str)


    @coroutine
    def insert_by_dict(self, db, param_dict, is_log=False):
        """ insert  2017.9.6"""
        sql = self.make_insert_sql_by_dict(db, param_dict)
        flag = yield self.execute(sql, param_dict)
        if is_log:
            app_log.info(("insert ?", flag, db, param_dict, "sql=", sql))
        raise Return(flag)


