# -*- coding:utf-8 -*- 
# --------------------
# Author:		
# Create:  2017/6/26 下午3:55
# Description:	
# --------------------
from tornado import escape
from tornado.gen import coroutine

from handlers import Route
from handlers import BaseADHandler
from config import DELETE_MODE
from ..model.CustomerModel import custom_model


@Route(r'admin/customer')
@Route(r'admin/customer/(\d+)')
class CustomerHandler(BaseADHandler):
    @coroutine
    def get(self, *args):
        """
        :获取所有用户:
            - GET: admin/customer?page_no=1&page_size=10
                   filter: customer_status 用户状态
                           user_grade 用户级别ID
                           assessment_type 会员评价分类ID
                           user_id 会员ID
                           company_name 公司名
        :获取指定用户:
            - GET: admin/customer/<user_id>
        """
        if args:
            result = yield custom_model.get_by_id(args[0])
            self.write_rows(rows=result)
        else:
            user_grade = self.get_argument('user_grade', '')
            user_type = self.get_argument('user_type', '')
            assessment_type = self.get_argument('assessment_type', '')
            user_id = self.get_argument('user_id', '')
            param_dict = {
                'page_no': int(self.get_argument('page_no', 1)),
                'page_size': int(self.get_argument('page_size', 10)),
                'customer_status': self.get_argument('customer_status', ''),
                'user_grade': int(user_grade) if user_grade else 0,
                'user_type': int(user_type) if user_type else 0,
                'assessment_type': int(assessment_type) if assessment_type else 0,
                'user_id': int(user_id) if user_id else 0,
                'company_name': self.get_argument('company_name', '')
            }
            result, count = yield custom_model.get_all(**param_dict)
            self.write_rows(rows={'customerList': result, 'count': count})

    @coroutine
    def post(self):
        """
        :管理员新增用户:
            - POST: admin/customer
            - param_dict : {'email': '', 'phone':'' , 'password': ''}
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=1, msg='Param can not be empty')
            return
        result = yield custom_model.add_user(**param_dict)
        if result == -1:
            self.write_rows(code=-1, msg='Register failed, DB error.')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')
        elif result == -3:
            self.write_rows(code=-1, msg='Email or phone has been used.')
        elif result == 1:
            self.write_rows(code=1, msg='Register success')

    @coroutine
    def put(self, *args):
        """
        :更新用户信息:
            - PUT: admin/customer/<user_id>
            - param_dict key:
                user_id, primary_sex, primary_xing, primary_ming, phone, primary_qq, tel,
                business_man, business_tel, technical_tel, technical_man, finance_man, finance_tel,
                company, delegate, country_id, province_id, city_id, address, rev_phone,
                user_type_id, grade_id, coin, star, pwd, user_site,
                confirm_site,  company_type_id, user_rank_type_id, comment
        :更新用户状态:
            - PUT: admin/customer?status_code=-1(禁用)|1(正常)&user_id=1,2,3...
        """
        status_code = self.get_argument('status_code', '')
        user_id = self.get_argument('user_id', '')
        if status_code and user_id:
            user_id_list = user_id.split(',')
            result = yield custom_model.update_user_status(user_id_list, status_code)
        else:
            param_dict = escape.json_decode(self.request.body)
            if not self.is_param_valid(param_dict):
                self.write_rows(code=1, msg='Param can not be empty')
                return
            result = yield custom_model.update_by_id(**param_dict)
        if result == 1 or result == 0:
            self.write_rows(msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Update db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')

    @coroutine
    def delete(self, *args):
        """
        :删除一个用户:
            - DELETE: admin/customer/<user_id>
        :批量删除用户:
            - DELETE: admin/customer?ids=<id1,id2,id3>
        """
        if args:
            ids = args[0]
        else:
            ids_str = self.get_argument('ids', '0').encode('utf-8')
            ids = filter(str.isdigit, ids_str.split(','))
        if DELETE_MODE:
            result = yield custom_model.delete_by_id(ids)
        else:
            result = yield custom_model.logic_delete(ids)
        if result >= 0:
            self.write_rows(msg='succeed delete:{0}'.format(result))
        elif result == -1:
            self.write_rows(code=-1, msg='Delete db error')



@Route(r'admin/info/customer')
@Route(r'admin/info/customer/(\d+)')
class CustomerLoginInfoHandler(BaseADHandler):
    @coroutine
    def get(self, *args):
        """
        :获取所有用户:
            - GET: admin/customer?email=xxxx
        :获取指定用户:
            - GET: admin/customer/<user_id>
        """
        if args:
            result = yield custom_model.get_login_info_by_id(args[0])
            self.write_rows(rows=result)
        else:
            email = self.get_argument('email', '')
            result = yield custom_model.get_login_info_by_email(email)
            self.write_rows(rows=result)