# -*- coding:utf-8 -*- 
# --------------------
# Author:		
# Create:  2017/6/28 下午3:12
# Description:	
# --------------------
from tornado.gen import coroutine, Return
from tornado.log import app_log

from models import BaseADModel


class UserTypeModel(BaseADModel):
    @coroutine
    def get_all(self):
        result = yield self.query(
            'SELECT _id, name FROM sys_user_type_config'
        )
        raise Return(result)

    @coroutine
    def update_by_id(self, **kwargs):
        try:
            row_count = yield self.update(
                'UPDATE sys_user_type_config SET name=%s WHERE _id=%s',
                (kwargs['name'], kwargs['_id'])
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)

    @coroutine
    def add_new(self, name):
        try:
            row_id = self.insert(
                'INSERT INTO sys_user_type_config (name) VALUES (%s)', name
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_id)

    @coroutine
    def delete_by_id(self, ids):
        """@param ids: 单个 ID 或 id list"""
        try:
            sql = 'DELETE FROM sys_user_type_config WHERE _id IN ('
            if isinstance(ids, list):
                length = len(ids)
                sql += ','.join(['%s'] * length) + ')'
            else:
                sql += '%s)'
            row_count = yield self.delete(sql, ids)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)


class UserRankTypeModel(BaseADModel):
    @coroutine
    def get_all(self):
        result = yield self.query(
            'SELECT _id, name FROM sys_user_rank_type_config'
        )
        raise Return(result)

    @coroutine
    def update_by_id(self, **kwargs):
        try:
            row_count = yield self.update(
                'UPDATE sys_user_rank_type_config SET name=%s WHERE _id=%s',
                (kwargs['name'], kwargs['_id'])
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)

    @coroutine
    def add_new(self, name):
        try:
            row_id = self.insert(
                'INSERT INTO sys_user_rank_type_config (name) VALUES (%s)', name
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_id)

    @coroutine
    def delete_by_id(self, ids):
        """@param ids: 单个 ID 或 id list"""
        try:
            sql = 'DELETE FROM sys_user_rank_type_config WHERE _id IN ('
            if isinstance(ids, list):
                length = len(ids)
                sql += ','.join(['%s'] * length) + ')'
            else:
                sql += '%s)'
            row_count = yield self.delete(sql, ids)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)


class UserGradeTypeModel(BaseADModel):
    @coroutine
    def get_all(self):
        result = yield self.query(
            'SELECT _id, name FROM sys_user_grade_config'
        )
        raise Return(result)

    @coroutine
    def update_by_id(self, **kwargs):
        try:
            row_count = yield self.update(
                'UPDATE sys_user_grade_config SET name=%s WHERE _id=%s',
                (kwargs['name'], kwargs['_id'])
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)

    @coroutine
    def add_new(self, name):
        try:
            row_id = self.insert(
                'INSERT INTO sys_user_grade_config (name) VALUES (%s)', name
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_id)

    @coroutine
    def delete_by_id(self, ids):
        """@param ids: 单个 ID 或 id list"""
        try:
            sql = 'DELETE FROM sys_user_grade_config WHERE _id IN ('
            if isinstance(ids, list):
                length = len(ids)
                sql += ','.join(['%s'] * length) + ')'
            else:
                sql += '%s)'
            row_count = yield self.delete(sql, ids)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)


class CompanyTypeModel(BaseADModel):
    @coroutine
    def get_all(self):
        result = yield self.query(
            'SELECT _id, name FROM sys_company_type_config'
        )
        raise Return(result)

    @coroutine
    def update_by_id(self, **kwargs):
        try:
            row_count = yield self.update(
                'UPDATE sys_company_type_config SET name=%s WHERE _id=%s',
                (kwargs['name'], kwargs['_id'])
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)

    @coroutine
    def add_new(self, name):
        try:
            row_id = self.insert(
                'INSERT INTO sys_company_type_config (name) VALUES (%s)', name
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_id)

    @coroutine
    def delete_by_id(self, ids):
        """@param ids: 单个 ID 或 id list"""
        try:
            sql = 'DELETE FROM sys_company_type_config WHERE _id IN ('
            if isinstance(ids, list):
                length = len(ids)
                sql += ','.join(['%s'] * length) + ')'
            else:
                sql += '%s)'
            row_count = yield self.delete(sql, ids)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(row_count)


user_type_model = UserTypeModel()
user_rank_type_model = UserRankTypeModel()
user_grade_type_model = UserGradeTypeModel()
company_type_model = CompanyTypeModel()
