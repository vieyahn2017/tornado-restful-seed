# -*- coding:utf-8 -*- 
# --------------------
# Author:		gxm1015@qq.com
# Description:	
# --------------------
import hashlib
from functools import wraps
from tornado.gen import coroutine, Return
from connproxy import StoreCache
from config import WS_CACHE_KEY


def cached(timeout=5 * 60, key=WS_CACHE_KEY):
    """
    A decorators can cache model result to memcached.
    :param timeout: cache expire time
    :param key: the cache's memcached key.
    """

    # XXX: 争对某个查询参数的不同生成唯一的缓存KEY,现使用参数的MD5值 6.14
    def cache_to_memcached(fun):
        @coroutine
        @wraps(fun)
        def decorators(self, *args, **kwargs):
            key_str = self.__class__.__name__.lower() + ':' + fun.__name__ + ':'
            if args:
                key_str += hashlib.md5(str(args)).hexdigest()
            if kwargs:
                key_str += hashlib.md5(str(kwargs)).hexdigest()
            cache_key = key.format(key_str)
            with StoreCache() as mc:
                cache_value = mc.get(cache_key)
            if cache_value is not None:
                raise Return(cache_value)
            cache_value = yield fun(self, *args, **kwargs)
            with StoreCache() as mc:
                mc.set(
                    cache_key,
                    cache_value,
                    timeout
                )
            raise Return(cache_value)

        return decorators

    return cache_to_memcached
