# -*-coding:utf-8 -*-
# @author:yanghao
# @created:20170426
# Description: http_fetch
from pprint import pprint
from tornado import escape
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.log import app_log

from config import MODULE_ADDRESS


class Fetcher(object):
    def __init__(self, host):
        self.host = host

    @coroutine
    def _fetch(self, url, method='get', body=None):
        fetch_url = "%s/%s" % (self.host, url)
        request = HTTPRequest(url=fetch_url, method=method.upper(), body=body)
        try:
            response = yield AsyncHTTPClient().fetch(request)
            response_body = escape.json_decode(response.body)
            code = response_body.get('code')
            rows = response_body.get('rows')
            # app_log.debug("receive_rows:%s %s" % (rows, type(rows)))
            results = {
                "rows": rows,
                "msg": response_body.get("msg"),
                "code": code,
                "url": response.request.url
            }
        except HTTPError as e:
            app_log.error(u'{0}: {1}  Msg: {2}'.format(method.upper(), fetch_url, e))
            raise Return({"url": fetch_url, "code": -1, "msg": e})
        else:
            app_log.debug(u"{0}: {1}  Code: {2}  MSG: {3}".format(
                method.upper(), fetch_url, code, response_body.get('msg'))
            )
            if body:
                pprint(escape.json_decode(body))
            raise Return(results)

    @coroutine
    def fetch_rows(self, url):
        results = yield self._fetch(url)
        raise Return(results)

    @coroutine
    def fetch_delete(self, url):
        results = yield self._fetch(url, 'delete')
        raise Return(results)

    @coroutine
    def fetch_post(self, url, body):
        results = yield self._fetch(url, 'post', escape.json_encode(body))
        raise Return(results)

    @coroutine
    def fetch_put(self, url, body):
        results = yield self._fetch(url, 'put', escape.json_encode(body))
        raise Return(results)


def get_module_url(module):
    _url, _port = MODULE_ADDRESS[module]
    return "http://%s:%s/api/v1" % (_url, _port)


webservices_fetcher = Fetcher(get_module_url('webservices'))
admin_fetcher = Fetcher(get_module_url("admin"))

# 保留，防报错
compute_fetcher = Fetcher(get_module_url("admin"))
network_fetcher = Fetcher(get_module_url("admin"))
storage_fetcher = Fetcher(get_module_url("admin"))
images_fetcher = Fetcher(get_module_url("admin"))
