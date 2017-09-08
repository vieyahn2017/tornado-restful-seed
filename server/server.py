#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2015-08-11 15:50:21
# Last modified:2017-06-09 10:08:08
# Filename:server.py
# Description:
from __future__ import absolute_import

from tornado.log import app_log
from tornado.options import define, options

from config import settings, DEFAULT_PORT
from connproxy import (install_dbpool, install_cache_pool)
from core import Application, context


def shutdown_handler():
    pass


def log_function(handler):
    if "debug" in settings and settings["debug"]:
        request_time = 1000.0 * handler.request.request_time()
        app_log.info("%d %s %.2fms", handler.get_status(), handler._request_summary(), request_time)


def set_service_status():
    from constant import CACHE_SERVER_UP, DATABASE_SERVER_UP
    from core import SystemStatus
    SystemStatus.set_cache_server_status(CACHE_SERVER_UP)
    SystemStatus.set_database_server_status(DATABASE_SERVER_UP)


def before_start(app):
    app.reg_shutdown_hook(shutdown_handler)
    install_dbpool()
    install_cache_pool()
    set_service_status()

    app.settings["log_function"] = log_function

    from concurrent.futures.thread import ThreadPoolExecutor
    works = app.settings["executor_number"]
    app.settings["executor"] = ThreadPoolExecutor(max_workers=works)
    context["executor"] = app.settings["executor"]


def test_mc():
    from utils import getmc
    client = getmc()
    print client
    print client.get_stats()

def main():
    # test_mc()
    options.logging = "debug"
    options.log_to_stderr = True
    define("address", default='0.0.0.0', help="run server as address")
    # define("port", default=DEFAULT_PORT, help="run server as port", type=int)
    # define("module", default='webservices', help="load specifical modules")
    define("module", default='admin', help="load specifical modules")
    define("port", default=30082, help="run server as port", type=int)
    define("debug", default=True, help="run as a debug model", type=bool)
    Application().before(before_start).start()



main()
