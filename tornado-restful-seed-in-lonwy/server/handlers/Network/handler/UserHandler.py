# -*- coding:utf-8 -*-
# --------------------
# Author:
# Description:	用户
# --------------------
import base64
import cStringIO as StringIO
import hashlib

from tornado import escape
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient
from tornado.web import MissingArgumentError

import utils
from config import MODULE_ADDRESS
from core import Session
from handlers import Route
from config import EMAIL_CODE_EXPIRE
from .BaseWSHandler import BaseWSHandler
from handlers import BaseADHandler
from ..model.UserModel import user_model, config_model, user_cache
from ..utils import captcha
from ..utils.mail import send_mail
from ..utils.token import generate_auth_token, verify_auth_token


@Route(r'webservices/accounts/balance')
class GetUserBalanceHandler(BaseWSHandler):
    @coroutine
    def get(self):
        res = yield user_model.get_user_balance(33)
        self.write_rows(rows=res)



@Route(r'webservices/accounts')
@Route(r'webservices/accounts/(\d+)')
class UserHandler(BaseWSHandler):
    @coroutine
    def get(self, user_id=None):
        """Get user info by id"""
        if not user_id:
            self.write_rows(code=-1, msg='Missing argument: user_id')
            return
        result = yield user_model.get_info_by_id(user_id)
        if not result:
            self.write_rows(code=-1, msg='Not found user')
            return
        self.write_rows(rows=result)

    @coroutine
    def post(self):
        """
        Register a new user.
        param(json) key:
        email, password, telephone, sms_verify_code, verify_key(client get from header: verify_key)
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=-1, msg="Param can not be empty.")
            return
        try:
            is_verified = user_cache.is_code_verified(
                param_dict['sms_verify_code'], param_dict['verify_key']
            )
            if not is_verified:
                self.write_rows(code=-1, msg='Check SMS code is right?')
                return
        except KeyError:
            self.write_rows(code=-1, msg='Missing argument: sys_verify_code, verify_key')
            return

        result = yield user_model.add_user(**param_dict)
        if result == -1:
            self.write_rows(code=-1, msg='Register failed, DB error.')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')
        elif result == -3:
            self.write_rows(code=-1, msg='Email or phone has been used.')
        elif result == 1:
            self.write_rows(code=1, msg='Register success')

    @coroutine
    def put(self):
        """
        Update user's info.
        param:{'id': id, 'field_name': 'password'|'email'|'phone'|'username',
         'value': new_value, ('old_password': 'pwd' | 'sms_verify_code': code), 'verify_key': verify_key}
        """
        param_dict = escape.json_decode(self.request.body)
        param_dict.update(id=self.user_id)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=-1, msg="Param can not be empty.")
            return
        try:
            field_name = param_dict['field_name']
            if field_name == 'password':
                check_param = {
                    'user_id': param_dict['id'],
                    'old_password': param_dict['old_password']
                }
                is_ok = yield self._check_old_password(**check_param)
                if not is_ok:
                    self.write_rows(code=-1, msg='Old password error.')
                    return
            elif field_name == 'email' or field_name == 'phone':
                is_verified = user_cache.is_code_verified(
                    param_dict['sms_verify_code'], param_dict['verify_key']
                )
                if not is_verified:
                    self.write_rows(code=-1, msg='Check SMS code is right?')
                    return
        except KeyError:
            self.write_rows(code=-1, msg='Missing argument')
            return

        result = yield user_model.update_user(**param_dict)
        if result == -2:
            self.write_rows(code=-1, msg='Missing argument')
        elif result == -1:
            self.write_rows(code=-1, msg='DB error')
        elif result == 0:
            self.write_rows(msg='Updated but no changes.')
        elif result == 1:
            self.write_rows(msg='Update success')

    @coroutine
    def _check_old_password(self, **kwargs):
        """if update password check old password is ok."""
        old_password_ok = yield user_model.check_old_password(**kwargs)
        if old_password_ok:
            raise Return(True)
        else:
            raise Return(False)

    @coroutine
    def delete(self):
        """Delete a user"""
        self.write_rows(msg='Method Not Allowed.')


@Route(r"webservices/accounts/check/(?P<field>email|phone)/(?P<value>.+)")
class UserCheckHandler(BaseWSHandler):
    # TODO check email and phone format is valid. 2017.6.11
    @coroutine
    def get(self, field='email', value=None):
        if field == 'email':
            res = yield user_model.get_user_hash_by_email(value)
        else:
            res = yield user_model.get_user_hash_by_phone(value)
        if res:
            self.write_rows(msg='User has registered.', rows={'isExist': True})
        else:
            self.write_rows(msg='{0} can use'.format(field), rows={'isExist': False})


@Route('webservices/verifycode')
class VerifyCodeHandler(BaseWSHandler):
    def get(self):
        output = StringIO.StringIO()
        im = captcha.create_validate_code()
        im[0].save(output, 'JPEG', quality=100)
        result = user_cache.set_verify_code(im[1])
        if result:
            self.set_header('verify_key', result)
        img_data = output.getvalue()
        output.close()
        self.write_rows(code=1, msg=base64.b64encode(img_data))

    @coroutine
    def post(self):
        """
        POST  校验前台输入的验证码
        param_dict {"verify_code": code, "verify_key": key}
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=-1, msg="Param can not be empty.")
            return
        try:
            is_verified = user_cache.is_code_verified(
                param_dict['verify_code'], param_dict['verify_key']
            )
            if not is_verified:
                self.write_rows(code=-1, msg="verify code is not matched or expired")
                return
        except KeyError:
            self.write_rows(code=-1, msg="Missing argument")
        else:
            self.write_rows(code=1)


@Route(r'webservices/accounts/login')
class LoginHandler(BaseWSHandler):
    @coroutine
    def post(self):
        """
        param: {
            'user_name': email or telephone,
            'password': password,
            'verify_code': verify code,
            'verify_key': verify key
         }
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=-1, msg="Param can not be empty.")
            return
        try:
            user_name = param_dict['user_name'].encode('utf-8').strip()
            is_verified = user_cache.is_code_verified(
                param_dict['verify_code'], param_dict['verify_key']
            )
            if user_name.startswith("email_"):
                user_name = user_name[6:]
                user_hash = hashlib.md5(user_name).hexdigest().encode('utf-8')
            elif user_name.startswith("phone_"):
                username = user_name.replace("phone_", "")
                result = yield user_model.get_user_hash_by_phone(username)
                if not result:
                    self.write_rows(code=-1, msg='User does not exist.')
                    return
                user_hash = result.get('user_hash')
            else:
                self.write_rows(code=-1, msg='Param error.')
                return

            login_res = yield user_model.user_login(user_hash, param_dict['password'].strip())
            if login_res == 1:
                user_info = yield user_model.get_info_by_hash(user_hash)
                Session.create_session(user_info, self)
                self.write_rows(msg=u'登陆成功', rows=user_info)
            elif login_res == -2:
                self.write_rows(code=-1, msg=u'用户名或密码错误')
            elif login_res == -1:
                self.write_rows(code=-1, msg=u'用户被禁用')
            elif login_res == 0:
                self.write_rows(code=-1, msg=u'用户未激活')
        except KeyError:
            self.write_rows(code=-1, msg='Missing argument.')


@Route(r"webservices/accounts/logout")
class LogoutHandler(BaseWSHandler):
    def get(self):
        Session.logout(self)
        self.write_response()


@Route(r'webservices/sms')
class SMSVerifyHandler(BaseWSHandler):
    @coroutine
    def get(self):
        """
        GET 生成短信验证码
        parm_dict {'flag': 1|2|3|4(1 注册, 2 找回密码,3 修改绑定手机, 4 设置新的手机), 'phone': phone}
        """
        #
        param_dict = {
            "phone": self.get_argument('phone', ''),
            "flag": self.get_argument('flag', '')
        }
        if not self.is_param_valid(param_dict):
            self.write_rows(code=-1, msg="Param: phone, flag can not be empty.")
            return
        # get sms conf info
        sms_config = yield config_model.get_sms_config()
        if not sms_config:
            self.write_rows(code=-1, msg="Get SMS server conf error.")
            return

        _time, _code = utils.get_verify_code()
        # get content, duration
        msg_res = yield config_model.get_verification_msg(
            param_dict['flag']
        )
        content = msg_res['content'].format(
            param_dict['phone'], _code,
            msg_res['duration']
        )
        # set sms _code to memcached
        verify_key = user_cache.set_verify_code(_code, msg_res['duration'])
        if verify_key:
            self.set_header('verify_key', verify_key)
        else:
            raise Exception('Cache server down.')
        # send sms
        url = sms_config['url'].format(
            sms_config['account'],
            sms_config['password'],
            param_dict['phone'],
            content
        )
        res = yield AsyncHTTPClient().fetch(url)
        if res.code == 200:
            self.write_rows(msg='ok')
        else:
            self.write_rows(code=-1, msg="send failed. the error code is {0}".format(res.code))

    @coroutine
    def post(self):
        """
        POST 校验短信验证码
        parm_dict {'verify_code': code, 'verify_key': key}
        """
        param_dict = escape.json_decode(self.request.body)
        if not self.is_param_valid(param_dict):
            self.write_rows(code=-1, msg="Param can not be empty.")
            return
        try:
            is_verified = user_cache.is_code_verified(
                param_dict['verify_code'], param_dict['verify_key']
            )
            if not is_verified:
                self.write_rows(code=-1, msg="The verify code does not match or expired")
                return
            else:
                self.write_rows(msg='ok')
        except KeyError:
            self.write_rows(code=-1, msg='Missing argument')


@Route(r'webservices/accounts/send-email')
class SendVerifyEmailHandler(BaseWSHandler):
    """
    用户更改邮箱流程:
    1. 进入邮箱更新页面, 发送更改邮箱短信验证码到用户手机.(调用发送短信验证码接口)
    2. 用户输入短信验证码.
    3. 验证成功, 进入新页面, 用户输入新邮箱, 点击确认提交, 调用发送激活Link 到新邮箱. (调用发送激活邮箱Link接口)
    4. 用户进入新邮箱, 点击激活Link后, 更新用户表邮箱地址, 更新邮箱激活状态.  (调用验证激活邮箱Link接口)

    """

    @coroutine
    def get(self):
        """verify email verify code"""
        try:
            verify_code = self.get_argument('verify_code')
            email = self.get_argument('email')
            print(verify_code, user_cache.get_verify_code(email.encode('utf-8')), email)
            if verify_code != user_cache.get_verify_code(email):
                self.write_rows(code=-1, msg='Email verify code error')
            else:
                self.write_rows(msg='verify code check succeed.')
        except MissingArgumentError as e:
            self.write_rows(code=-1, msg='Missing argument:{0}'.format(e))

    @coroutine
    def post(self):
        """
        Send email
        param_dict {'email': email address, 'type':activate_email|reset_password}
        """
        try:
            param_dict = escape.json_decode(self.request.body)
            if not self.is_param_valid(param_dict):
                self.write_rows(code=-1, msg="Param can not be empty.")
                return
            result = None
            email_server = yield config_model.get_email_server()
            if param_dict['type'] == 'activate_email':
                user_id = None
                if self.current_user:
                    user_id = self.user_id
                result = yield self._send_activate_mail(param_dict['email'], email_server, user_id)
            elif param_dict['type'] == 'reset_password':
                result = yield self._send_reset_password_mail(param_dict['email'], email_server)
            elif param_dict['type'] == 'update_email':
                result = yield self._send_update_mail_code(param_dict['email'], email_server)

            if result:
                self.write_rows(msg="Email send succeed.")
            else:
                self.write_rows(code=-1, msg="Send email failed. ")
        except KeyError as e:
            self.write_rows(code=-1, msg='Missing argument: {0}'.format(e))

    @coroutine
    def _send_activate_mail(self, email, email_server, user_id):
        email_token = generate_auth_token({'user_id': user_id, 'email': email})
        # TODO config content, ip in config file.
        title = "邮箱认证"
        content = """<html><body>
            <p>尊敬的{0}用户:</p><p>请点击以下链接，完成邮箱激活。</p>
            <button > <a href = {1}>激活邮箱</a></button>
            <p>或复制以下链接到浏览器以完成验证：</p>
            <a href={1}>{1}</a>
            <p>链接2小时内有效</p>
            </body></html>"""
        activate_url = "http://{0}:{1}/api/v1/webservices/accounts/confirm-email/{2}".format(
            MODULE_ADDRESS['webservices'][0], MODULE_ADDRESS['webservices'][1], email_token
        )
        content = content.format(email, activate_url)
        result = yield self.executor.submit(
            send_mail,
            email_server['mail_host'], email_server['mail_user'], email_server['mail_password'],
            email_server['mail_postfix'], [email], title, content, subtype="html"
        )
        raise Return(result)

    @coroutine
    def _send_reset_password_mail(self, email, email_server):
        # TODO config content, ip in config file.
        _time, _code = utils.get_verify_code()
        user_cache.set(email, _code, EMAIL_CODE_EXPIRE)
        title = "重置密码"
        content = """<html><body>
                <p>尊敬的{0}用户:</p><p>您正在重置密码</p>
                <p>验证码为: {1}</p>
                <p>{2}分钟内有效</p>
                </body></html>"""
        content = content.format(email, _code, EMAIL_CODE_EXPIRE / 60)
        result = yield self.executor.submit(
            send_mail,
            email_server['mail_host'], email_server['mail_user'], email_server['mail_password'],
            email_server['mail_postfix'], [email], title, content, subtype="html"
        )
        raise Return(result)

    @coroutine
    def _send_update_mail_code(self, email, email_server):
        _time, _code = utils.get_verify_code()
        user_cache.set(email, _code, EMAIL_CODE_EXPIRE)
        title = "更新邮箱"
        content = """<html><body>
                    <p>尊敬的{0}用户:</p><p>您正在更新邮箱</p>
                    <p>验证码为: {1}</p>
                    <p>{2}分钟内有效</p>
                    </body></html>"""
        content = content.format(email, _code, EMAIL_CODE_EXPIRE / 60)
        result = yield self.executor.submit(
            send_mail,
            email_server['mail_host'], email_server['mail_user'], email_server['mail_password'],
            email_server['mail_postfix'], [email], title, content, subtype="html"
        )
        raise Return(result)


@Route(r'webservices/accounts/confirm-email/(.*)')
class ActiveEmailHandler(BaseWSHandler):
    @coroutine
    def get(self, token):
        """Activate user email"""
        verify_result = verify_auth_token(token)
        if verify_result == -1:
            self.write_rows(code=-1, msg='Signature expired.')
        elif verify_result == -2:
            self.write_rows(code=-1, msg='Bad signature.')
        else:
            user_id = verify_result['user_id']
            email = verify_result['email']
            result = yield user_model.activate_email(email, user_id)
            if result == 1 or result == 0:
                self.write_rows(msg='Activate email success.')
            elif result == -1:
                self.write_rows(code=-1, msg='update db error')


@Route(r'webservices/accounts/reset-password')
class ResetPasswordHandler(BaseWSHandler):
    # XXX: Is this necessary?
    @coroutine
    def get(self):
        try:
            user_name = self.get_argument('userName')
            value = None
            value_type = None
            if user_name.startswith("email_"):
                value = user_name[6:]
                value_type = 'email'
            elif user_name.startswith("phone_"):
                value = user_name.replace("phone_", "")
                value_type = 'phone'
            else:
                self.write_rows(code=-1, msg='Param error.')
                return
            result = yield user_model.get_email_and_phone(value, value_type)
            self.write_rows(rows=result)
        except MissingArgumentError as e:
            self.write_rows(code=-1, msg='Missing argument: {0}'.format(e))

    @coroutine
    def post(self):
        """
        重置密码.
         param_dict {
         'new_password': pwd,
         'reset_type': email|phone,
         'value': user's email or phone
         'verify_code': verify code get from phone or mail box.
         'verify_key': if reset type is phone, must get verify key from http header.
         }
        """
        try:
            param_dict = escape.json_decode(self.request.body)
            if not self.is_param_valid(param_dict):
                self.write_rows(code=-1, msg="Param can not be empty.")
                return
            if param_dict['reset_type'] == 'email':
                cache_verify_code = user_cache.get(param_dict['value'])
                if cache_verify_code != param_dict['verify_code'].lower().encode('utf-8'):
                    self.write_rows(code=-1, msg='Email verify code error.')
                    return
            elif param_dict['reset_type'] == 'phone':
                is_verified = user_cache.is_code_verified(
                    param_dict['verify_code'], param_dict['verify_key']
                )
                if not is_verified:
                    self.write_rows(code=-1, msg='Verify code not matched')
                    return

            result = yield user_model.reset_password(
                param_dict['reset_type'],
                param_dict['value'],
                param_dict['new_password']
            )
            if result == 1:
                self.write_rows(msg='Rest password succeed.')
            elif result == 0:
                self.write_rows(msg="Update success but password not change.")
            else:
                self.write_rows(code=-1, msg='Reset failed: {0}'.format(result))
        except KeyError as e:
            self.write_rows(code=-1, msg='Missing argument:{0}'.format(e))


# @Route(r'webservices/accounts/reset-password-by-email/(.*)')
# class EmailResetPassword(BaseWSHandler):
#     @coroutine
#     def get(self, token):
#         """Reset password by email"""
#         verify_result = verify_auth_token(token)
#         if verify_result == -1:
#             self.write_rows(code=-1, msg='Signature expired.')
#         elif verify_result == -2:
#             self.write_rows(code=-1, msg='Bad signature.')
#         else:
#             result = yield user_model.reset_password('email', verify_result, 'new_password')
#             if result == 1 or result == 0:
#                 self.write_rows(msg='Password reset succeed.')
#             elif result == -1:
#                 self.write_rows(code=-1, msg='update db error.')
