#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2014-08-16 22:39:36
# Last modified:2017-06-06 18:44:06
# Filename:utils.py
# Description:

import imghdr
import random
import tempfile
import time
from base64 import encodestring
from hashlib import sha256, md5
from uuid import uuid1

import yaml
from tornado.log import app_log

import config
import uuid
RANDOM_SEED = "1234567890abcdefghjklmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"


def save_avatar(photodata):
    ext = is_image(stream=photodata)
    if ext:
        filename = "%s.%s" % (get_tempname(), ext)
        fullpath = config.UPLOAD_PATH % filename
        with open(fullpath, "wb") as avatar:
            avatar.write(photodata)
        return unicode(config.UPLOAD_URL % filename)
    else:
        raise Exception("file format error")


def get_mqclient():
    from core import context
    return context.get("message_backend")


def load_rbacfile():
    from config import RBAC_FILE, RBAC_FILE2
    try:
        rbac_dict = yaml.load(file(RBAC_FILE))
        return rbac_dict["rights"]
    except IOError as ioex:
        rbac_dict = yaml.load(file(RBAC_FILE2))
        return rbac_dict["rights"]
        # app_log.exception(ioex.message)


def async_client():
    from tornado.httpclient import AsyncHTTPClient
    return AsyncHTTPClient(max_body_size=1024 * 100)


def is_image(filename=None, stream=None):
    return imghdr.what(filename, stream)


def valid_filename(ext):
    ext = ext.lower()
    if ext not in config.VALID_FILE_EXT:
        raise Exception(500, "invalid fiename")


def get_tempname():
    return next(tempfile._get_candidate_names())


def module_resolver(namespace):
    namespace_parts = namespace.split(".")
    module_name = ".".join(namespace_parts[0:-1])
    cls_name = namespace_parts[-1]
    try:
        module = __import__(module_name, fromlist=["*"])
        if hasattr(module, cls_name):
            return getattr(module, cls_name)
    except Exception as ex:
        app_log.error("resolve %s failed with exception %s" % (namespace, ex))


def is_dirty(model_obj):
    obj_info = model_obj.__storm_object_info__
    return obj_info.get("sequence")


def get_verify_code(length=6):
    code = []
    for _ in range(0, length):
        code.append(random.choice('1234567890'))
    return int(time.time()), "".join(code)


def build_all_hash(model, func_name, args, kwargs):
    remain_args = args[1:]
    if remain_args:
        condition_hash = "".join(str(hash(obj)) for obj in remain_args)

    if kwargs:
        condition_hash = hash(tuple(zip(kwargs.iterkeys(), kwargs.itervalues())))

    return "%s.%s.%s" % (model.__storm_table__, func_name, str(condition_hash))


def build_paging_hash(model, func_name, args, kwargs):
    key = "%s.%s.%d"
    table = model.__storm_table__
    form = args[1]
    rs = args[2]
    startindex, endindex = parsepage(form)
    rs = rs[startindex:endindex]
    rs_hash = hash(rs.get_select_sql())
    return key % (table, func_name, rs_hash)


def build_filter_by_hash(model, func_name, args, kwargs):
    key = "%s.%s.%d"
    table = model.__storm_table__
    form = args[1]
    return key % (table, func_name, hash(form))


def build_password(pwd):
    from config import settings
    salt = settings["salt"]
    key = "%s%s" % (salt, pwd.strip())
    return unicode(sha256(key).hexdigest())


def build_random_passwd(length=8):
    plain_pwd = "".join((random.choice(RANDOM_SEED) for _ in xrange(length)))
    hash_pwd = unicode(sha256(plain_pwd).hexdigest())
    return plain_pwd, hash_pwd


def build_token(factor=""):
    key = "%s_%s" % (str(uuid1()), factor)
    return encodestring(sha256(key).digest()).strip()


def build_md5(obj):
    return encodestring(md5(obj).hexdigest()).strip()


class Singleton(type):
    def __call__(clazz, *args, **kwargs):
        if hasattr(clazz, "_instance"):
            return clazz._instance
        else:
            clazz._instance = super(Singleton, clazz).__call__(*args, **kwargs)
            return clazz._instance


def getstore():
    from config import dbConf
    from tornado_mysql import pools
    # pools.DEBUG = True #调试模式
    return pools.Pool(dbConf['conn'], **dbConf['params'])



from contextlib import contextmanager

class ClientPoolEmptyOnWIndows(object):
    """only used fow windows not Error.  yanghao.8.31"""
    def get_stats(self):
        return 1

    @contextmanager
    def reserve(self):
        try:
            yield iter('abcdefg')
        finally:
            print('abcdefg!')


def getmc():
    """
    @return: Memcached ClientPool
    """
    try:
        from pylibmc import Client, ClientPool
        from config import cacheServers, MC_POOL_SIZE
        adv_setting = {"cas": True, "tcp_nodelay": True, "ketama": True}
        mc = Client(cacheServers, binary=True, behaviors=adv_setting)
        return ClientPool(mc, MC_POOL_SIZE)
    except ImportError:
        return ClientPoolEmptyOnWIndows()

