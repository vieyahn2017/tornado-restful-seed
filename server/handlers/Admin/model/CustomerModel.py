# -*- coding:utf-8 -*- 
# --------------------
# Author:		
# Create:  2017/6/26 下午3:55
# Description:	
# --------------------
import hashlib

from tornado.gen import coroutine, Return
from tornado.log import app_log
from tornado_mysql import IntegrityError

from models import BaseADModel

class CustomerModel(BaseADModel):
    @coroutine
    def get_by_id(self, user_id):
        result = yield self.get(
            """SELECT a._id, b.username, a.email, b.password,   -- login info
            c.primary_sex, c.primary_xing, c.primary_ming, a.phone, c.primary_qq,  -- contact info
            c.tel,   -- notify info   phone: a.phone, email: a.email.
            c.business_man, c.business_tel, c.technical_tel, c.technical_man, c.finance_man, c.finance_tel,  -- other contact
            d.company, d.delegate, d.country_id, d.province_id, d.city_id, d.address, d.phone as rev_phone,   -- contract info
            e.user_type_id, e.grade_id, e.coin, e.star, e.pwd, e.site as user_site,  -- user grade info
            f.site as confirm_site,  f.company_type_id, user_rank_type_id, f.comment   -- assessment info
            FROM sys_user a 
            LEFT JOIN sys_user_info b 
            ON a._id = b._id 
            LEFT JOIN sys_user_other_contact c 
            ON b._id = c._id 
            LEFT JOIN sys_user_contract d 
            ON c._id = d._id 
            LEFT JOIN sys_user_grade_info e 
            ON d._id =  e._id 
            LEFT JOIN sys_user_assessment f 
            ON e._id = f._id  
            WHERE a._id = %s """, int(user_id)
        )
        raise Return(result)

    @coroutine
    def get_all(self, **kwargs):
        # XXX: 用户现在生效中的订单数（过滤分条: buy_state='1' and end_date> time.time()）,
        # 存在支付成功, 但资源未分配的情况, 目前订单表中没有相关字段表示订单资源分配成功了.
        filter_str = ''
        sql_str = """SELECT a._id, b.username, d.company, f.site,  e1.name AS grade_name, e2.name AS type_name, 
                  e.star, f1.name AS assessment_type, g.manager_no, b.flag, e.coin, 
                  (SELECT COUNT(1) FROM webservice_orders WHERE user_id=a._id) AS all_order_count,
                  (SELECT COUNT(1) FROM webservice_orders WHERE user_id=a._id 
                  AND buy_state=\'1\' AND end_date > UNIX_TIMESTAMP(NOW())) AS in_service_count 
                  FROM sys_user a 
                  LEFT JOIN sys_user_info b  ON a._id = b._id 
                  LEFT JOIN sys_user_other_contact c  ON b._id = c._id 
                  LEFT JOIN sys_user_contract d ON c._id = d._id 
                  LEFT JOIN sys_user_grade_info e ON d._id =  e._id 
                  LEFT JOIN sys_user_grade_config e1 ON e.grade_id = e1._id 
                  LEFT JOIN sys_user_type_config e2 ON e.user_type_id = e2._id 
                  LEFT JOIN sys_user_assessment f ON e._id = f._id 
                  LEFT JOIN sys_user_rank_type_config f1 ON f.user_rank_type_id = f1._id 
                  LEFT JOIN sys_user_manager g ON g.user_id = a._id 
                  WHERE a.is_valid != \'0\' """
        order_by_str = ' ORDER BY b.reg_date DESC LIMIT %(from_no)s, %(page_size)s '
        kwargs.update(from_no=kwargs['page_size'] * (kwargs['page_no'] - 1))
        if kwargs['company_name']:
            filter_str = ' AND d.company LIKE %(company_name)s '
            kwargs.update(company_name='%' + kwargs['company_name'] + '%')
        elif kwargs['user_id']:
                filter_str = ' AND a._id = %(user_id)s '
        else:
            filter_str = self._get_filter_sql(**kwargs)
        result = yield self.query(sql_str + filter_str + order_by_str, kwargs)
        count = yield self._get_user_count(filter_str, **kwargs)
        raise Return((result, count))

    @staticmethod
    def _get_filter_sql(**param_dict):
        sql_str = ''
        filter_list = []
        if param_dict['customer_status']:
            filter_list.append(' b.flag=%(customer_status)s ')
        if param_dict['user_grade']:
            filter_list.append(' e1._id=%(user_grade)s ')
        if param_dict['user_type']:
            filter_list.append(' e2._id=%(user_type)s ')
        if param_dict['assessment_type']:
            filter_list.append(' f1._id=%(assessment_type)s ')
        if filter_list:
            sql_str += ' AND ' + ' AND '.join(filter_list)
        return sql_str

    @coroutine
    def _get_user_count(self, filter_str, **kwargs):
        result = yield self.get(
            """SELECT count(1) as count FROM sys_user a 
            LEFT JOIN sys_user_info b ON a._id = b._id 
            LEFT JOIN sys_user_other_contact c ON b._id = c._id 
            LEFT JOIN sys_user_contract d ON c._id = d._id 
            LEFT JOIN sys_user_grade_info e ON d._id =  e._id 
            LEFT JOIN sys_user_grade_config e1 ON e.grade_id = e1._id 
            LEFT JOIN sys_user_type_config e2 ON e.user_type_id = e2._id 
            LEFT JOIN sys_user_assessment f ON e._id = f._id 
            LEFT JOIN sys_user_rank_type_config f1 ON f.user_rank_type_id = f1._id 
            LEFT JOIN sys_user_manager g ON g.user_id = a._id 
            WHERE a.is_valid != \'0\' """ + filter_str, kwargs
        )
        raise Return(result['count'])

    @coroutine
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
                "INSERT INTO sys_user (email, phone, user_hash) VALUES (%s,%s,%s)",
                (kwargs['email'], kwargs['telephone'], user_hash)
            )
            user_row_id = cur1.lastrowid
            user_info_dict = {
                "_id": user_row_id,
                "user_hash": user_hash,
                "username": kwargs['email'].split('@')[0],
                "password": kwargs['password'],
                "email_token": '0'
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
            raise Return(-2)
        except IntegrityError as e:
            app_log.error(e)
            yield ctx.rollback()
            raise Return(-3)
        except Exception as e:
            app_log.error(e)
            yield ctx.rollback()
            raise Return(-1)
        else:
            raise Return(1)

    @coroutine
    def update_user_status(self, user_id_list, status_code):
        """用户禁用(-1)/解禁(1)"""
        try:
            for user_id in user_id_list:
                row_count = yield self.update(
                    'UPDATE sys_user_info SET flag=%s WHERE _id=%s', (status_code, int(user_id))
                )
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(1)

    @coroutine
    def update_by_id(self, **kwargs):
        # TODO 确认是否可以修改用户登陆相关信息. 6.28
        try:
            row1 = yield self.update(
                """UPDATE sys_user_other_contact SET business_man=%s, business_tel=%s, technical_tel=%s, technical_man=%s, 
                finance_man=%s, finance_tel=%s, primary_sex=%s, primary_xing=%s, primary_ming=%s WHERE _id=%s """,
                (kwargs['business_man'], kwargs['business_tel'], kwargs['technical_tel'], kwargs['technical_man'], 
                 kwargs['finance_man'], kwargs['finance_tel'], kwargs['primary_sex'], kwargs['primary_xing'], kwargs['primary_ming'], kwargs['user_id'])
            )
            row2 = yield self.update(
                """UPDATE sys_user_contract SET company=%s, delegate=%s, country_id=%s, province_id=%s, city_id=%s, address=%s, phone=%s WHERE _id=%s """,
                (kwargs['company'], kwargs['delegate'], kwargs['country_id'], kwargs['province_id'], kwargs['city_id'], kwargs['address'], kwargs['phone'], kwargs['user_id'])
            )
            row3 = yield self.update(
                """UPDATE sys_user_grade_info SET user_type_id=%s, grade_id=%s, coin=%s, star=%s, pwd=%s, site=%s WHERE _id=%s""",
                (kwargs['user_type_id'], kwargs['grade_id'], kwargs['coin'], kwargs['star'], kwargs['pwd'], kwargs['user_site'], kwargs['user_id'])
            )
            row4 = yield self.update(
                """UPDATE sys_user_assessment SET company_type_id=%s, user_rank_type_id=%s, site=%s, comment=%s WHERE _id=%s""",
                (kwargs['company_type_id'], kwargs['user_rank_type_id'], kwargs['confirm_site'], kwargs['comment'], kwargs['user_id'])
            )
        except KeyError as e:
            app_log.error(e)
            raise Return(-2)
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(1)

    @coroutine
    def logic_delete(self, id_list):
        """删除用户-逻辑删除"""
        try:
            for user_id in id_list:
                yield self.update(
                    """UPDATE sys_user SET is_valid = \'0\' WHERE _id=%s""", int(user_id)
                )
        except Exception as e:
            app_log.error(e)
            raise Return(-1)
        else:
            raise Return(1)

    @coroutine
    def delete_by_id(self, ids):
        """@param ids: 单个 ID 或 id list"""
        ctx = yield self.begin()
        try:
            sql_list = [
                'DELETE FROM sys_user WHERE _id IN (',
                'DELETE FROM sys_user_info WHERE _id IN (',
                'DELETE FROM sys_user_other_contact WHERE _id IN(',
                'DELETE FROM sys_user_contract WHERE _id IN(',
                'DELETE FROM sys_user_grade_info WHERE _id IN(',
                'DELETE FROM sys_user_assessment WHERE _id IN('
            ]
            if isinstance(ids, list):
                length = len(ids)
                sub_sql = ','.join(['%s'] * length) + ')'
                sql_list = map(lambda x: x + sub_sql, sql_list)
            else:
                sql_list = map(lambda x: x + '%s)', sql_list)
            for sql in sql_list:
                yield ctx.execute(sql, ids)
            yield ctx.commit()
        except Exception as e:
            app_log.error(e)
            yield ctx.rollback()
            raise Return(-1)
        else:
            raise Return(1)



    @coroutine
    def get_login_info_by_id(self, user_id):
        result = yield self.get(
            """SELECT a._id, b.username, a.email, b.password, a.phone 
            FROM sys_user a 
            LEFT JOIN sys_user_info b 
            ON a._id = b._id  
            WHERE a._id = %s """, int(user_id)
        )
        raise Return(result)

    @coroutine
    def get_login_info_by_email(self, email):
        result = yield self.get(
            """SELECT a._id, b.username, a.email, b.password, a.phone  
            FROM sys_user a 
            LEFT JOIN sys_user_info b 
            ON a._id = b._id  
            WHERE a.email = %s """, email
        )
        raise Return(result)


custom_model = CustomerModel()
