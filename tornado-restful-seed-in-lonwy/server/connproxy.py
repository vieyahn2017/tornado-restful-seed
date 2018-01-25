#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2014-06-06 13:59:37
# Last modified:2017-06-06 14:45:32
# Filename:connproxy.py
# Description:

from __future__ import absolute_import, with_statement

from core import context

__all__ = ("StoreContext",)


def install_dbpool():
    from utils import getstore
    context['store'] = getstore()


def install_cache_pool():
    from utils import getmc
    context['mc'] = getmc()


def get_proxy_mc():
    return context['mc']


class StoreCache(object):
    def __init__(self):
        self._store = None

    def __enter__(self):
        try:
            with context['mc'].reserve() as mc:
                self._store = mc
        except:
            raise
        print  self._store
        return self._store

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class StoreContext(object):
    def __init__(self, dictCursor=True):
        self._store = None
        self._dictCursor = dictCursor

    def __enter__(self):
        try:
            self._store = context['store']
            if self._dictCursor:
                from tornado_mysql.cursors import DictCursor
                self._store.connect_kwargs['cursorclass'] = DictCursor
        except:
            raise
        return self._store

    def __exit__(self, exc_type, exc_value, traceback):
        pass
