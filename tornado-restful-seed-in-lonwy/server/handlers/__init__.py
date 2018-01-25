#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2015-08-26 13:51:41
# Last modified:2017-06-07 11:16:26
# Filename:handlers.BaseHandler.py
# Description:
from __future__ import absolute_import

import os
import re
from cStringIO import StringIO

import tornado.httpclient
import tornado.web
from tornado import httputil
from tornado.gen import coroutine
from tornado.log import app_log

import config
import constant
import utils
from auth import AuthenticationException
from config import API_VERSION
from connproxy import StoreCache
from core import context, Session


class Route(object):
    urls = []

    def __call__(self, url, name=None):
        def _(cls):
            if url.startswith("/"):
                _url = r"%s" % url
            else:
                _url = r"/api/%s/%s" % (API_VERSION, url)
            self.urls.append(tornado.web.URLSpec(_url, cls, name=name))
            return cls

        return _


Route = Route()


class WireCallable(object):
    def __init__(self, callableobj, args, kwargs):
        self._callback = callableobj
        self._before = None
        self._after = None
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        if self._before:
            self._before()
        try:
            return self._callback(*self._args, **self._kwargs)
        except:
            raise
        finally:
            if self._after:
                self._after()

    def before_call(self, callback):
        self._before = callback
        return self

    def after_call(self, callback):
        self._after = callback
        return self


class BaseHandler(tornado.web.RequestHandler):
    def check_xsrf_cookie(self):
        return False

    def prepare(self):
        self.current_user = self.get_current_user()
        for middleware in context["middleware"]:
            middleware.process_request(self)

    def finish(self):
        for middleware in context["middleware"]:
            middleware.process_response(self)
        super(BaseHandler, self).finish()

    def write_error(self, status_code, **kwargs):
        exc_cls, exc_instance, trace = kwargs.get("exc_info")
        if not hasattr(exc_instance, "status_code"):
            exc_instance.status_code = 500
        status_code = exc_instance.status_code
        if status_code not in httputil.responses:
            status_code = 500

        if len(exc_instance.args) == 2:
            _, errmsg = exc_instance.args
        else:
            if hasattr(exc_instance, "message"):
                errmsg = exc_instance.message
                if not errmsg and hasattr(exc_instance, "log_message"):
                    errmsg = exc_instance.log_message
            else:
                errmsg = exc_instance.log_message

        self.write(dict(msg=errmsg, code=status_code))
        self.set_status(status_code)

    def write_user_error(self, msg="", code=500):
        self.set_status(code)
        self.write(dict(msg=msg))

    def get_header(self, key):
        value = self.request.headers.get(key)
        return value if value and value != "null" else None

    def get_token(self):
        token_name = self.application.settings["token_name"]
        return self.get_header(token_name)

    def is_superuser(self):
        return self.current_user.is_superuser

    def has_roles(*roles):
        return True

    def has_role(self, role):
        return role in self.current_user.roles

    def has_perm(self, perm_names):
        path = self.request.path.split("/")[2]

        if isinstance(perm_names, (str, unicode)):
            perm_names = [perm_names]

        for rightinfo in self.current_user.rights:
            # [{"action":"CRUD", "url":"class"}]
            if path in rightinfo:
                actions = rightinfo["action"]
                for perm in perm_names:
                    if actions.find(perm) > -1:
                        return True
            return False
        else:
            return False

    def get_session(self):
        return Session.get_session(self)

    def get_current_user(self):
        session = self.get_session()
        if session:
            return session.user

    @property
    def user_id(self):
        if self.current_user:
            return self.current_user['_id']
        else:
            raise AuthenticationException(403, 'need login')

    @property
    def user_info(self):
        if self.current_user:
            return self.current_user
        else:
            raise AuthenticationException(403, 'Get user info need login')

    def need_login(self):
        self.write_user_error(code=403, msg="please relogin with your cred")

    @staticmethod
    def get_page_query(form):
        form_params = {
            "curpage": form.curpage.data,
            "perpage": form.perpage.data,
            "totalpage": form.totalpage.data,
            "keywords": form.keywords.data
        }
        return form_params

    def write_rows(self, code=1, msg='', form=None, rows=()):
        response = {"msg": msg, "code": code, "rows": rows}
        if form:
            response.update(self.get_page_query(form))
        self.write(response)

    def write_response(self, **kwargs):
        # kwargs.update(dict(code=200))
        self.write(kwargs)

    @property
    def executor(self):
        return self.application.settings["executor"]

    def async(self, callableobj, *args, **kwargs):
        wired_callback = WireCallable(callableobj, args, kwargs)
        wired_callback.before_call(self.before).after_call(self.after)
        future = self.executor.submit(wired_callback)
        return future

    def before(self):
        from core import cache_client
        return cache_client()

    def after(self):
        from core import remove_cache_client
        remove_cache_client()

    @property
    def cache_server(self):
        with StoreCache() as mc:
            return mc



class BaseADHandler(BaseHandler):
    """
    Base handler class for Admin.
    Other handler in Admin must inherit from this class.
    """

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header(
            "Access-Control-Expose-Headers",
            'Content-Type, X-Xsrf-Token,x-xss-protection,'
            'content-length,X-Requested-With, content-length,X-Requested-With, verify_key'
        )
        self.set_header(
            "Access-Control-Allow-Headers",
            'Content-Type, X-Xsrf-Token,x-xss-protection,'
            'content-length,X-Requested-With, content-length,X-Requested-With, verify_key'
        )
        self.set_header("Access-Control-Allow-Methods", "PUT, DELETE, POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    @staticmethod
    def is_param_valid(param_dict):
        """check param_dict value"""
        if "" in param_dict.values():
            return False
        else:
            return True



@Route(r"/")
class IndexHandler(BaseHandler):
    def get(self):
        path = []
        modules = context['module'].split(",")
        _base_url = ["/api/%s/%s" %(API_VERSION, m.lower()) for m in modules]

        for x in self.application.handlers[0][1]:
            for _url in _base_url:
                if (x._path.startswith(_url)):
                    path.append(x._path)
        self.write_rows(rows=path)


# @Route(r"/api/uploadstream")
# @tornado.web.stream_request_body
# class UploadStreamHandler(BaseHandler):
#     def prepare(self):
#         super(UploadStreamHandler, self).prepare()
#         content_dispostion = self.get_header("Content-Disposition")
#         content_length = self.get_header("Content-Length")
#         content_type = self.get_header("Content-Type")
#         if all([content_dispostion, content_length, content_type]):
#             find_filename = re.compile('name="(.*)"')
#             search_filename = find_filename.search(content_dispostion)
#             if search_filename:
#                 name, ext = os.path.splitext(search_filename.groups()[0])
#                 self.tempfilename = "%s%s" % (utils.get_tempname(), ext)
#                 self.localfile = config.UPLOAD_TEMP_PATH % self.tempfilename
#                 self.output = open(self.localfile, "wb")
#         else:
#             raise ValueError("param error")
#
#     def data_received(self, data):
#         self.output.write(data)
#
#     def post(self):
#         self.output.close()
#         if utils.is_image(self.localfile):
#             download_url = config.UPLOAD_URL % self.tempfilename
#             self.write_response(err="", msg=download_url)
#         else:
#             app_log.warn("%s no image file" % self.localfile)
#             self.write_user_error("image format error")
#
#
#  @Route(r"/api/uploadavatar")
# @tornado.web.stream_request_body
# class UploadAvatarHandler(UploadStreamHandler):
#     def prepare(self):
#         super(UploadAvatarHandler, self).prepare()
#         self.tempfilename = "%s" % utils.get_tempname()
#         self.localfile = config.UPLOAD_TEMP_PATH % self.tempfilename
#         self.output = open(self.localfile, "wb")
#
#     def post(self):
#         self.output.close()
#         ext = utils.is_image(self.localfile)
#         if ext:
#             self.tempfilename = "%s.%s" % (self.tempfilename, ext)
#             final_filename = config.UPLOAD_TEMP_PATH % self.tempfilename
#             utils.move_file(self.localfile, final_filename)
#             download_url = config.UPLOAD_URL % self.tempfilename
#             self.write_response(status=1, url=download_url)
#         else:
#             app_log.warn("%s no image file" % self.localfile)
#             utils.rm_file(self.tempfilename)
#             self.write_user_error(status=-1, msg="image format error")
#
#
# @Route(r"/api/uploadurl")
# class UploadUrl(BaseHandler):
#     def write_img(self, response):
#         if response.code == 200:
#             ext = utils.is_image(stream=response.body)
#             if not ext:
#                 return
#             tempname = "%s.%s" % (utils.get_tempname(), ext)
#             img_path = config.UPLOAD_TEMP_PATH % tempname
#             download_url = config.UPLOAD_URL % tempname
#             self.files.append(download_url)
#             with open(img_path, "wb") as img:
#                 img.write(response.body)
#
#     @coroutine
#     def post(self):
#         url = self.get_argument("urls")
#         self.files = []
#         if url:
#             url = url.split("|")
#             if len(url) > 10:
#                 self.write_user_error(msg="too many url")
#             else:
#                 httpclient = utils.async_client()
#                 imgs = yield [httpclient.fetch(img_url) for img_url in url]
#                 for img in imgs:
#                     self.write_img(img)
#                 url_strings = "|".join(self.files)
#                 self.write(url_strings)
#
#
# @Route(r"/api/upload")
# @tornado.web.stream_request_body
# class UploadHandler(BaseHandler):
#     def prepare(self):
#         super(UploadHandler, self).prepare()
#         print self.request.headers
#         self.mimetype = self.request.headers.get("Content-Type")
#         if self.mimetype is None:
#             raise Exception(500, "params error")
#         self.boundary = "--%s" % (self.mimetype[self.mimetype.find("boundary") + 9:])
#         self.state = constant.PARSE_READY
#         self.output = None
#         self.find_filename = re.compile('filename="(.*)"')
#         self.find_mimetype = re.compile('Content-Type: (.*)')
#         self.find_field = re.compile('name="(.*)"')
#         self.files = []
#
#     def post(self):
#         download_urls = [config.UPLOAD_URL % fname for fname in self.files]
#         self.write_response(rows=download_urls)
#
#     def valid_filename(self, ext):
#         ext = ext.lower()
#         if ext not in config.VALID_FILE_EXT:
#             raise Exception(500, "invalid fiename")
#
#     def createfile(self, filename):
#         import tempfile
#         import os
#         filename, ext = os.path.splitext(filename)
#         self.valid_filename(ext)
#         tempfilename = "%s%s" % (next(tempfile._get_candidate_names()), ext)
#         self.files.append(tempfilename)
#         filename = config.UPLOAD_TEMP_PATH % tempfilename
#         self.output = open(filename, "wb")
#
#     def data_received(self, data):
#         buff = data.split(self.boundary)
#         for index, part in enumerate(buff):
#             if part:
#                 if part == "--\r\n":
#                     break
#                 elif self.state == constant.PARSE_FILE_PENDING:
#                     if len(buff) > 1:
#                         self.output.write(part[:-2])
#                         self.output.close()
#                         self.state = constant.PARSE_READY
#                     else:
#                         self.output.write(part)
#
#                 elif self.state == constant.PARSE_READY:
#                     stream = StringIO(part)
#                     stream.readline()
#                     form_data_type_line = stream.readline()
#                     if form_data_type_line.find("filename") > -1:
#                         filename = re.search(self.find_filename, form_data_type_line).groups()[0].strip()
#                         self.createfile(filename)
#                         content_type_line = stream.readline()
#                         mimetype = re.search(self.find_mimetype, content_type_line).groups()[0]
#                         app_log.debug("%s with %s" % (filename, mimetype.strip()))
#                         stream.readline()
#                         body = stream.read()
#                         if len(buff) > index + 1:
#                             self.output.write(body[:-2])
#                             self.state = constant.PARSE_READY
#                         else:
#                             self.output.write(body)
#                             self.state = constant.PARSE_FILE_PENDING
#                     else:
#                         stream.readline()
#                         form_name = re.search(self.find_field, form_data_type_line).groups()[0]
#                         form_value = stream.readline()
#                         self.state = constant.PARSE_READY
#                         app_log.debug("%s=%s" % (form_name.strip(), form_value.strip()))
