# -*- coding:utf-8 -*-
# --------------------
# Author:
# Description:	用户模型, 短信接口, 短信模版, 邮件服务器信息
# --------------------
import hashlib
import time
import uuid

from tornado import gen
from tornado.log import app_log
from tornado_mysql import IntegrityError

from  config import VERIFY_CODE_EXPIRE, HALF_DAY

from models import BaseADModel
from ..utils.cache import cached
from models import BaseADModel

class UserModel(BaseADModel):
    @gen.coroutine
    def get_user_balance(self, user_id):
        res = yield self.get(
            'SELECT money FROM sys_user_info '
            'WHERE _id=%s', user_id
        )
        raise gen.Return(res)

    @gen.coroutine
    def get_info_by_id(self, user_id):
        result = yield self.get(
            "SELECT u._id, u.email, u.phone, i.username, i.grade, "
            "i.roles_id, i.money, i.reg_date, (CASE WHEN i.email_token = '1' THEN 1 ELSE 0 END) AS email_status "
            "FROM sys_user u "
            "LEFT JOIN sys_user_info i "
            "ON u.user_hash = i.user_hash "
            "WHERE u._id = %s ", user_id
        )
        raise gen.Return(result)

    @gen.coroutine
    def get_info_by_hash(self, user_hash):
        result = yield self.get(
            "SELECT u._id, u.email, u.phone, i.username, i.grade, "
            "i.roles_id, i.money, i.reg_date "
            "FROM sys_user u "
            "LEFT JOIN sys_user_info i "
            "ON u.user_hash = i.user_hash "
            "WHERE u.user_hash = %s ", user_hash
        )
        raise gen.Return(result)

    @gen.coroutine
    def get_user_hash_by_phone(self, phone):
        result = yield self.get(
            "SELECT user_hash  "
            "FROM sys_user "
            "WHERE phone=%s", phone
        )
        raise gen.Return(result)

    @gen.coroutine
    def get_user_hash_by_email(self, email):
        result = yield self.get(
            "SELECT user_hash  "
            "FROM sys_user "
            "WHERE email=%s", email
        )
        raise gen.Return(result)

    @gen.coroutine
    def get_user_status_by_id(self, user_id):
        result = yield self.get(
            "SELECT flag "
            "FROM sys_user_info "
            "WHERE _id=%s", user_id
        )
        if not result:
            raise gen.Return(-2)
        else:
            raise gen.Return(int(result.get('flag')))

    @gen.coroutine
    def get_email_and_phone(self, value, value_type):
        result = None
        if value_type == 'phone':
            result = yield self.get(
                'SELECT email, phone FROM sys_user WHERE phone= %s ', value
            )
        elif value_type == 'email':
            user_hash = hashlib.md5(value).hexdigest().encode('utf-8')
            result = yield self.get(
                'SELECT email, phone FROM sys_user WHERE user_hash=%s', user_hash
            )
        raise gen.Return(result)

    @gen.coroutine
    def user_login(self, user_hash, password):
        """user_hash, password是否正确"""
        result = yield self.get(
            "SELECT _id, flag "
            "FROM sys_user_info "
            "WHERE user_hash=%s "
            "AND password=%s",
            (user_hash, password)
        )
        if result:
            raise gen.Return(int(result.get('flag')))
        else:
            raise gen.Return(-2)

    @gen.coroutine
    def add_user(self, **kwargs):
        """
        Add a new user to database.
        先存入phone，email和邮箱生成的user_hash，获得_id (sys_user)
        再存入用户的_id, user_hash, password，email_token (sys_user_info)
        @param kwargs {
            'email': mail,
            'phone': phone,
            'user_hash:  md5(email),
            'password': password  # 前端加密
        }
        """
        user_hash = hashlib.md5(kwargs['email']).hexdigest()
        ctx = yield self.begin()
        try:
            cur1 = yield ctx.execute(
                "INSERT INTO sys_user (email, phone, user_hash) "
                "VALUES (%s,%s,%s)",
                (kwargs['email'], kwargs['telephone'], user_hash)
            )
            user_row_id = cur1.lastrowid
            user_info_dict = {
                "_id": user_row_id,
                "user_hash": user_hash,
                "username": kwargs['email'].split('@')[0],
                "password": kwargs['password'],
                "email_token": str(uuid.uuid1())
            }
            cur2 = yield ctx.execute(
                "INSERT INTO sys_user_info "
                "(_id, username, user_hash, password, email_token, reg_date, flag) "
                "VALUES (%(_id)s, %(username)s, %(user_hash)s, %(password)s, "
                "%(email_token)s, UNIX_TIMESTAMP(NOW()), '1')", user_info_dict
            )
            yield ctx.execute('INSERT INTO sys_user_other_contact (_id) VALUES (%s)', user_row_id)
            yield ctx.execute('INSERT INTO sys_user_contract (_id) VALUES (%s)', user_row_id)
            yield ctx.execute('INSERT INTO sys_user_grade_info (_id) VALUES (%s)', user_row_id)
            yield ctx.execute('INSERT INTO sys_user_assessment (_id) VALUES (%s)', user_row_id)

            yield ctx.commit()
        except KeyError as e:
            app_log.error(e)
            yield ctx.rollback()
            raise gen.Return(-2)
        except IntegrityError as e:
            app_log.error(e)
            yield ctx.rollback()
            raise gen.Return(-3)
        except Exception as e:
            app_log.error(e)
            yield ctx.rollback()
            raise gen.Return(-1)
        else:
            raise gen.Return(1)

    @gen.coroutine
    def activate_user(self, user_id):
        """ activate user, set flag = 1"""
        try:
            row_count = yield self.update(
                "UPDATE sys_user_info "
                "SET email_token='', flag='1' "
                "WHERE _id=%s;", user_id
            )
        except Exception as e:
            app_log.error(e)
        else:
            raise gen.Return(row_count)

    @gen.coroutine
    def get_user_email_token(self, user_id):
        res = yield self.get(
            "SELECT email_token, flag "
            "FROM sys_user_info "
            "WHERE _id = %s", user_id
        )
        raise gen.Return(res)

    @gen.coroutine
    def activate_email(self, email, user_id):
        """
        If user_id is not None, this method do change email process and activate it.
        else the function do activate email process.
        """
        if user_id:
            result = yield self._change_email_and_activate(user_id, email)
        else:
            result = yield self._activate_email(email)
        raise gen.Return(result)

    @gen.coroutine
    def _change_email_and_activate(self, user_id, email):
        """
        1. update table sys_user's filed user_hash and email.
        2. update table sys_user_info's field user_hash and set email_token = '1'
        """
        ctx = yield self.begin()
        try:
            user_hash = hashlib.md5(email).hexdigest()
            cur1 = yield ctx.execute(
                "UPDATE sys_user "
                "SET user_hash=%s, email=%s where _id=%s ",
                (user_hash, email, user_id)
            )
            cur2 = yield ctx.execute(
                "UPDATE sys_user_info "
                "SET email_token='1', user_hash=%s "
                "WHERE _id=%s",
                (user_hash, user_id)
            )
            yield ctx.commit()
        except Exception as e:
            app_log.error(e)
            yield ctx.rollback()
            raise gen.Return(-1)
        else:
            raise gen.Return(1)

    @gen.coroutine
    def _activate_email(self, email):
        email_hash = yield self.get_user_hash_by_email(email)
        try:
            row_count = yield self.update(
                "UPDATE sys_user_info "
                "SET email_token='1' "
                "WHERE user_hash=%s", email_hash['user_hash']
            )
        except Exception as e:
            app_log.error(e)
            raise gen.Return(-1)
        else:
            raise gen.Return(row_count)

    @gen.coroutine
    def check_old_password(self, **kwargs):
        result = yield self.get(
            "SELECT _id FROM sys_user_info "
            "WHERE _id =%s AND password=%s",
            (kwargs['user_id'], kwargs['old_password'])
        )
        raise gen.Return(result)

    @gen.coroutine
    def update_password(self, **kwargs):
        try:
            row_count = 0
            res = yield self.get(
                "SELECT _id FROM sys_user_info "
                "WHERE _id =%s AND password=%s",
                (kwargs['user_id'], kwargs['old_password'])
            )
            if res:
                row_count = yield self.update(
                    "UPDATE sys_user_info "
                    "SET password=%s WHERE _id=%s",
                    (kwargs['new_password'], kwargs['user_id'])
                )
            else:
                row_count = -3  # old password error
        except KeyError:
            raise gen.Return(-2)  # missing argument
        except Exception as e:
            app_log.error(e)
            raise gen.Return(-1)  # db error
        else:
            raise gen.Return(row_count)  # 1 or 0 if 0 new password equals old password.

    @gen.coroutine
    def reset_password(self, reset_type, value, new_password):
        """
            @param reset_type: email|phone
            @param value: user's email or phone
            @param new_password: password
        """
        try:
            result = -1
            if reset_type == 'email':
                user_hash = yield self.get_user_hash_by_email(value)
                result = yield self.update(
                    "UPDATE sys_user_info "
                    "SET password = %s "
                    "WHERE user_hash = %s ", (new_password, user_hash['user_hash'])
                )
            elif reset_type == 'phone':
                user_hash = yield self.get_user_hash_by_phone(value)
                result = yield self.update(
                    "UPDATE sys_user_info "
                    "SET password = %s "
                    "WHERE user_hash = %s", (new_password, user_hash['user_hash'])
                )
        except Exception as e:
            app_log.error("Reset password failed!", e)
            raise gen.Return(-1)
        else:
            raise gen.Return(result)

    @gen.coroutine
    def update_email(self, user_id, email):
        try:
            yield self.update(
                "UPDATE sys_user SET email=%s "
                "WHERE _id=%s", (email, user_id)
            )
            flag = True
        except Exception as e:
            app_log.error(("Update email failed! ", user_id, e))
            flag = False
        raise gen.Return(flag)

    @gen.coroutine
    def update_user(self, **kwargs):
        """
        update table sys_user or sys_user_info.
        @param: kwargs: {
            'id': 1,
            'field_name': 'password'|'email'|'phone'|'username',
            'value': 'new_password'
        }
        """
        try:
            field_name = kwargs['field_name']
            if field_name not in ["password", "email", "phone", "username"]:
                app_log.error(("update_user error, the key is not supported ? ", field_name))
                raise gen.Return(-3)

            if field_name == 'email' or field_name == 'phone':
                sql_str = "UPDATE sys_user SET {0}=%s WHERE _id=%s".format(field_name)
                row_count = yield self.update(sql_str, (kwargs['value'], kwargs['id']))
            else:
                sql_str = "UPDATE sys_user_info SET {0}=%s WHERE _id=%s".format(field_name)
                row_count = yield self.update(sql_str, (kwargs['value'], kwargs['id']))
        except KeyError as e:
            app_log.error(e)
            raise gen.Return(-2)
        except Exception as e:
            app_log.error(e)
            raise gen.Return(-1)
        else:
            raise gen.Return(row_count)


class ConfigModel(BaseADModel):
    """
    短信接口, 短信模版, 邮件服务器信息, 目前只有获取方法
    """

    @cached(HALF_DAY)
    @gen.coroutine
    def get_verification_msg(self, msg_type):
        """取得短信通知内容"""
        res = yield self.get(
            "SELECT content, duration "
            "FROM sys_verification_msg "
            "WHERE TYPE = %s AND flag='1'", msg_type
        )
        raise gen.Return(res)

    @cached(HALF_DAY)
    @gen.coroutine
    def get_email_server(self):
        """获取邮件服务配置信息"""
        res = yield self.get(
            "SELECT mail_host, mail_user, mail_password, mail_postfix "
            "FROM sys_email_config WHERE flag='1' LIMIT 1"
        )
        raise gen.Return(res)

    @cached(HALF_DAY)
    @gen.coroutine
    def get_sms_config(self):
        """获取短信发关接口配置信息"""
        res = yield self.get(
            "SELECT account, password, url "
            "FROM sys_sms_config "
            "WHERE flag='1' AND _id=2"
        )
        raise gen.Return(res)


class UserCacheModel(BaseADModel):
    """Some Cache operation for User."""

    def get_verify_code(self, verify_key):
        """
        Get verify code from memcached
        @param verify_key: verify code's memcached key.
        """
        return self.cache_server.get(verify_key)

    def set_verify_code(self, verify_code, exptime=VERIFY_CODE_EXPIRE):
        """Set verify code to memcached. if cached success return the memcached key."""
        verify_code = self._format_verify_code(verify_code)
        key = self._get_unique_key(verify_code)
        result = self.cache_server.set(
            key,
            verify_code,
            exptime
        )
        if result:
            return key
        else:
            app_log.error('Cache verify code error')

    def set(self, key, verify_code, exptime):
        result = self.cache_server.set(
            key, verify_code, exptime
        )
        if not result:
            raise Exception('Cache mail verify code error.')

    def is_code_verified(self, verify_code, verify_key):
        """
        Check verify code
        @param verify_code: verify code from user input.
        @param verify_key: memcached key from http header verify_key.
        """
        verify_code = self._format_verify_code(verify_code)
        cache_verify_code = self.get_verify_code(verify_key)
        if verify_code == cache_verify_code:
            return True
        else:
            return False

    @staticmethod
    def _get_unique_key(verify_code):
        """Get a unique key use MAC address and time.time()"""
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        time_str = str(time.time())
        return hashlib.md5(mac + time_str + verify_code).hexdigest()

    @staticmethod
    def _format_verify_code(verify_code):
        return verify_code.lower().encode('utf-8')


user_model = UserModel()
user_cache = UserCacheModel()
config_model = ConfigModel()
