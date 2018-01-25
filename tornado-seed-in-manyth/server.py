# -*- coding: utf-8 -*- 
# --------------------
# Author:   yh001
# Description:  
# --------------------

import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options

from handler import TaxGpsCollector
from handler import PublishTaxiWeijieHandler
from log.mylogger import logger

define("port", default=9031, help="run on the given port", type=int)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("hello, welcome to [GpsCollecter]!")
        
class MyApplication(tornado.web.Application):
    def __init__(self):
        handlers =[
                    (r"/", IndexHandler),
                    (r"/collect", TaxGpsCollector),
                    (r"/analysis/publish", PublishTaxiWeijieHandler),
                    ]
        setting = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            )
        tornado.web.Application.__init__(self,handlers,**setting)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(MyApplication())
    http_server.listen(options.port)
    logger.info("the app is running at: %s" % options.port)
    tornado.ioloop.IOLoop.instance().start()