# -*- coding:utf-8 -*- 
# --------------------
# Author:		
# Create:  2017/6/28 下午3:12
# Description: 用户相关配置
# --------------------
from tornado import escape
from tornado.gen import coroutine

from handlers import Route
from handlers import BaseADHandler
from ..model.UserConfigModel import (company_type_model, user_grade_type_model,
                                     user_rank_type_model, user_type_model)



@Route(r'admin/setting/company-type')
@Route(r'admin/setting/company-type/(\d+)')
class MailSettingHandler(BaseADHandler):
    @coroutine
    def get(self):
        """
        :获取公司类型列表:
            - GET: admin/setting/company-type
        """
        result = yield company_type_model.get_all()
        self.write_rows(rows=result)

    @coroutine
    def post(self):
        """
        :新增公司类型:
            - POST: admin/setting/company-type
            | param_dict {'name': ''}
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield company_type_model.add_new(**param_dict)
        if result > 1:
            self.write_rows(rows=result, msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Insert db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def put(self, _id):
        """
        :更新类型:
            - PUT: admin/setting/company-type/<_id>
            | param_dict {'_id': '', 'name': ''}
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield company_type_model.update_by_id(**param_dict)
        if result == 1 or result == 0:
            self.write_rows(msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Update db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def delete(self, *args):
        """
        :删除一条:
            - DELETE: admin/setting/company-type/<_id>
        :批量删除:
            - DELETE: admin/setting/company-type?ids=<id1,id2,id3>
        """
        if args:
            ids = args[0]
        else:
            ids_str = self.get_argument('ids', 0).encode('utf-8')
            ids = filter(str.isdigit, ids_str.split(','))
        result = yield company_type_model.delete_by_id(ids)
        if result >= 0:
            self.write_rows(msg='succeed delete:{0}'.format(result))
        elif result == -1:
            self.write_rows(code=-1, msg='Delete db error')


@Route(r'admin/setting/user-grade')
@Route(r'admin/setting/user-grade/(\d+)')
class UserGradeTypeHandler(BaseADHandler):
    @coroutine
    def get(self):
        """
        :获取用户等级列表:
            - GET: admin/setting/user-grade
        """
        result = yield user_grade_type_model.get_all()
        self.write_rows(rows=result)

    @coroutine
    def post(self):
        """
        param_dict {
            'name': ''
        }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield user_grade_type_model.add_new(**param_dict)
        if result > 1:
            self.write_rows(rows=result, msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Insert db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def put(self, _id):
        """
        @param _id:
        param_dict {
            '_id': '',
            'name': ''
        }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield user_grade_type_model.update_by_id(**param_dict)
        if result == 1 or result == 0:
            self.write_rows(msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Update db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def delete(self, *args):
        if args:
            ids = args[0]
        else:
            ids_str = self.get_argument('ids', 0).encode('utf-8')
            ids = filter(str.isdigit, ids_str.split(','))
        result = yield user_grade_type_model.delete_by_id(ids)
        if result >= 0:
            self.write_rows(msg='succeed delete:{0}'.format(result))
        elif result == -1:
            self.write_rows(code=-1, msg='Delete db error')


@Route(r'admin/setting/rank-type')
@Route(r'admin/setting/rank-type/(\d+)')
class MailSettingHandler(BaseADHandler):
    @coroutine
    def get(self):
        result = yield user_rank_type_model.get_all()
        self.write_rows(rows=result)

    @coroutine
    def post(self):
        """
        param_dict {
            'name': ''
        }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield user_rank_type_model.add_new(**param_dict)
        if result > 1:
            self.write_rows(rows=result, msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Insert db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def put(self, _id):
        """
        @param _id:
        param_dict {
            '_id': '',
            'name': ''
        }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield user_rank_type_model.update_by_id(**param_dict)
        if result == 1 or result == 0:
            self.write_rows(msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Update db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def delete(self, *args):
        if args:
            ids = args[0]
        else:
            ids_str = self.get_argument('ids', 0).encode('utf-8')
            ids = filter(str.isdigit, ids_str.split(','))
        result = yield user_rank_type_model.delete_by_id(ids)
        if result >= 0:
            self.write_rows(msg='succeed delete:{0}'.format(result))
        elif result == -1:
            self.write_rows(code=-1, msg='Delete db error')


@Route(r'admin/setting/user-type')
@Route(r'admin/setting/user-type/(\d+)')
class MailSettingHandler(BaseADHandler):
    @coroutine
    def get(self):
        result = yield user_type_model.get_all()
        self.write_rows(rows=result)

    @coroutine
    def post(self):
        """
        param_dict {
            'name': ''
        }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield user_type_model.add_new(**param_dict)
        if result > 1:
            self.write_rows(rows=result, msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Insert db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def put(self, _id):
        """
        @param _id:
        param_dict {
            '_id': '',
            'name': ''
        }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield user_type_model.update_by_id(**param_dict)
        if result == 1 or result == 0:
            self.write_rows(msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Update db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def delete(self, *args):
        if args:
            ids = args[0]
        else:
            ids_str = self.get_argument('ids', 0).encode('utf-8')
            ids = filter(str.isdigit, ids_str.split(','))
        result = yield user_type_model.delete_by_id(ids)
        if result >= 0:
            self.write_rows(msg='succeed delete:{0}'.format(result))
        elif result == -1:
            self.write_rows(code=-1, msg='Delete db error')
