# -*- coding:utf-8 -*- 
# --------------------
# Author:		gxm1015@qq.com
# Create:  2017/6/29 下午3:51
# Description:	
# --------------------
from tornado.gen import coroutine, Return
from tornado.log import app_log
from tornado_mysql import IntegrityError

from connproxy import StoreContext
from models import BaseADModel

import traceback


class OrderStatusModel(BaseADModel):
    @coroutine
    def get_all(self):
        result = yield self.query(
            'SELECT _id, name FROM order_status '
        )
        raise Return(result)

class OrderContractStatusModel(BaseADModel):
    @coroutine
    def get_all(self):
        result = yield self.query(
            'SELECT _id, name FROM contract_status '
        )
        raise Return(result)


class OrderModel(BaseADModel):

    @coroutine
    def get_one(self, _id, is_log=False):
        result = yield self.get("""SELECT o._id, o.order_no, os.name AS order_status_name, 
                                    o.order_time, DATE_FORMAT(FROM_UNIXTIME(o.order_time), '%%Y/%%m/%%d %%h:%%i') AS order_time_fmt,
                                    o.take_time, DATE_FORMAT(FROM_UNIXTIME(o.take_time), '%%Y/%%m/%%d %%h:%%i') AS take_time_fmt,
                                    o.take_man, o.verify_man,
                                    o.user_id, ui.username, u.email, u.phone, 
                                    p.product_id, p.buy_number, p.product_serial_no, 
                                    p.total_money, p.currency_unit,
                                    f.discount, f.score_deduction, f.tax, f.logistics_expense, f.packing_expense, 
                                    f.total_payment, f.actual_payment, f.unpaid_total, f.payment_time, f.finance_verify_man,
                                    fvs.name AS finance_verify_status_name,
                                    fcs.name AS finance_charge_status_name, 
                                    fct.name AS finance_charge_type_name, 
                                    v.title, v.content, v.`comment`, t.contract_no, t.company, 
                                    ts.name AS contract_status_name, 
                                    r.receiver, r.receive_address, r.receive_phone,
                                    l.logistics_company, l.logistics_no, l.delivery_time, l.delivery_man, 
                                    lm.name AS logistics_delivery_mode_name
                                    FROM order_info o
                                    LEFT JOIN order_status os ON os._id=o.order_status_id 
                                    LEFT JOIN sys_user u ON u._id=o.user_id  
                                    LEFT JOIN sys_user_info ui ON ui._id=o.user_id  
                                    LEFT JOIN order_product_info p ON p._id=o._id
                                    LEFT JOIN order_finance_info f ON f.order_id=o._id 
                                    LEFT JOIN finance_verify_status fvs ON fvs._id=f.finance_verify_status_id
                                    LEFT JOIN finance_charge_status fcs ON fcs._id=f.finance_charge_status_id
                                    LEFT JOIN finance_charge_type fct ON fct._id=f.finance_charge_type_id
                                    LEFT JOIN order_invoice_info v ON v.order_id=o._id 
                                    LEFT JOIN order_contract_info t ON t.order_id=o._id 
                                    LEFT JOIN contract_status ts ON t.contract_status_id =ts._id 
                                    LEFT JOIN order_receive_info r ON r.order_id=o._id 
                                    LEFT JOIN order_logistics_info l ON l.order_id=o._id 
                                    LEFT JOIN logistics_delivery_mode lm ON l.delivery_mode_id=lm._id 
                                    WHERE o._id=%s;""", (_id,))
        if is_log:
            app_log.info(("get_one : ", _id, result))
        raise Return(result)


    @coroutine
    def get_all(self, **kwargs):
        """SQL原始语句为
        DATE_FORMAT(FROM_UNIXTIME(1495437314), '%Y/%m/%d %h:%i') 
        但是在Tornado-MySQL要改成%%，
        不然报错：ValueError: unsupported format character 'Y' (0x59) at index 153
        """
        filter_str = ''
        sql_str = """SELECT o._id, o.order_no, s.name AS order_status_name, 
                    o.order_time, DATE_FORMAT(FROM_UNIXTIME(o.order_time), '%%Y/%%m/%%d %%h:%%i') AS order_time_fmt, 
                    u.username, 
                    p.name AS product_name, 
                    c.name AS product_category_name ,
                    t.name AS product_type_name, 
                    i.buy_number, 
                    i.total_money, i.currency_unit,
                    cs.name AS finance_charge_status_name
                    FROM order_info o
                    LEFT JOIN order_status s ON s._id=o.order_status_id  
                    LEFT JOIN sys_user_info u ON u._id=o.user_id  
                    LEFT JOIN order_product_info i ON i._id=o._id
                    LEFT JOIN product p ON p._id=i.product_id 
                    LEFT JOIN product_type t ON t._id=p.product_type_id 
                    LEFT JOIN product_category c ON c._id=p.product_category_id 
                    LEFT JOIN order_finance_info f ON f.order_id=o._id 
                    LEFT JOIN finance_charge_status cs ON cs._id=f.finance_charge_status_id
                    WHERE o.deleted!=1 """
        order_by_str = ' ORDER BY o._id DESC LIMIT %(from_no)s, %(page_size)s '
        kwargs.update(from_no=kwargs['page_size'] * (kwargs['page_no'] - 1))
        filter_str = self._get_filter_sql(**kwargs)
        result = yield self.query(sql_str + filter_str + order_by_str, kwargs)
        count = yield self._get_user_count(filter_str, **kwargs)
        raise Return((result, count))


    @staticmethod
    def _get_filter_sql(**param_dict):
        sql_str = ''
        filter_list = []
        if param_dict['order_status_id']:
            filter_list.append(' o.order_status_id =%(order_status_id)s ')
        if param_dict['product_type_id']:
            filter_list.append(' p.product_type_id=%(product_type_id)s ')
        if param_dict['product_category_id']:
            filter_list.append(' p.product_category_id=%(product_category_id)s ')
        if param_dict['finance_charge_status_id']:
            filter_list.append(' cs._id=%(finance_charge_status_id)s ')
        if filter_list:
            sql_str += ' AND ' + ' AND '.join(filter_list)
        return sql_str

    @coroutine
    def _get_user_count(self, filter_str, **kwargs):
        result = yield self.get("""SELECT count(1) as count FROM order_info o
                                    LEFT JOIN order_status s ON s._id=o.order_status_id  
                                    LEFT JOIN order_product_info i ON i._id=o._id
                                    LEFT JOIN product p ON p._id=i.product_id 
                                    LEFT JOIN product_type t ON t._id=p.product_type_id 
                                    LEFT JOIN product_category c ON c._id=p.product_category_id 
                                    LEFT JOIN order_finance_info f ON f.order_id=o._id 
                                    LEFT JOIN finance_charge_status cs ON cs._id=f.finance_charge_status_id
                                    WHERE o.deleted!=1 """ + filter_str, kwargs
        )
        raise Return(result['count'])


    @coroutine
    def get_by_order_no(self, order_no):
        sql_str = """SELECT o._id, o.order_no, s.name AS order_status_name, 
                    o.order_time, DATE_FORMAT(FROM_UNIXTIME(o.order_time), '%%Y/%%m/%%d %%h:%%i') AS order_time_fmt, 
                    u.username, 
                    p.name AS product_name, 
                    c.name AS product_category_name ,
                    t.name AS product_type_name, 
                    i.buy_number, 
                    i.total_money, i.currency_unit,
                    cs.name AS finance_charge_status_name
                    FROM order_info o
                    LEFT JOIN order_status s ON s._id=o.order_status_id  
                    LEFT JOIN sys_user_info u ON u._id=o.user_id  
                    LEFT JOIN order_product_info i ON i._id=o._id
                    LEFT JOIN product p ON p._id=i.product_id 
                    LEFT JOIN product_type t ON t._id=p.product_type_id 
                    LEFT JOIN product_category c ON c._id=p.product_category_id 
                    LEFT JOIN order_finance_info f ON f.order_id=o._id 
                    LEFT JOIN finance_charge_status cs ON cs._id=f.finance_charge_status_id
                    WHERE o.deleted!=1 AND o.order_no=%s"""
        result = yield self.query(sql_str, order_no)
        raise Return(result)



    def _filter_param_and_update_pid(self, param_dict, order_id, filter_flag=True, value=None):
        if filter_flag:
            self.filter_param_by_value(param_dict, value)
        param_dict.update({"order_id": order_id})

    @coroutine
    def add_order(self, param_dict):
        """
            cursor = yield ctx.execute(
                "INSERT INTO order_info (user_id, order_no, order_time, take_time, order_status_id, take_man, verify_man) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (param_dict['user_id'], order_info_dict['order_no'], order_info_dict['order_time'], order_info_dict['take_time'], order_info_dict['order_status_id'], order_info_dict['take_man'], order_info_dict['verify_man'])
            )
            order_id = cursor.lastrowid
            9.6把user_id字段提前加入order_info_dict，还是调用make_insert_sql_by_dict生成sql语句方便一些


            order_product_info这个表有6个字段：
            product_id, product_serial_no, buy_number, total_money, currency_unit, after_sale_duration`
            之前的update只更新的前三个 > 9.6 扩成6个
            total_money, currency_unit在之前的get_all里面有用到

        """
        order_info_dict = param_dict["order_info_dict"]
        order_info_dict['user_id'] = param_dict['user_id']
        if order_info_dict['order_status_id'] == -1:
            order_info_dict['order_status_id'] = 1
        self.filter_param_by_value(order_info_dict)

        order_product_info_dict = param_dict["order_product_info_dict"]
        order_finance_info_dict = param_dict["order_finance_info_dict"]
        order_invoice_info_dict = param_dict["order_invoice_info_dict"]
        order_contract_info_dict = param_dict["order_contract_info_dict"]
        order_receive_info_dict = param_dict["order_receive_info_dict"]
        order_logistics_info_dict = param_dict["order_logistics_info_dict"]


        ctx = yield self.begin()
        try:
            sql_01 = self.make_insert_sql_by_dict("order_info", order_info_dict)
            cur_01 = yield ctx.execute(sql_01, order_info_dict)
            order_id = cur_01.lastrowid

            self.filter_param_by_value(order_product_info_dict)
            order_product_info_dict["_id"] = order_id
            self._filter_param_and_update_pid(order_finance_info_dict, order_id)
            self._filter_param_and_update_pid(order_invoice_info_dict, order_id, filter_flag=False)
            self._filter_param_and_update_pid(order_contract_info_dict, order_id)
            self._filter_param_and_update_pid(order_receive_info_dict, order_id, filter_flag=False)
            self._filter_param_and_update_pid(order_logistics_info_dict, order_id)

            sql_02 = self.make_insert_sql_by_dict("order_product_info",  order_product_info_dict)
            sql_03 = self.make_insert_sql_by_dict("order_finance_info", order_finance_info_dict)
            sql_04 = self.make_insert_sql_by_dict("order_invoice_info", order_invoice_info_dict)
            sql_05 = self.make_insert_sql_by_dict("order_contract_info", order_contract_info_dict)
            sql_06 = self.make_insert_sql_by_dict("order_receive_info", order_receive_info_dict)
            sql_07 = self.make_insert_sql_by_dict("order_logistics_info", order_logistics_info_dict)

            yield ctx.execute(sql_02, order_product_info_dict)
            yield ctx.execute(sql_03, order_finance_info_dict)
            yield ctx.execute(sql_04, order_invoice_info_dict)
            yield ctx.execute(sql_05, order_contract_info_dict)
            yield ctx.execute(sql_06, order_receive_info_dict)
            yield ctx.execute(sql_07, order_logistics_info_dict)

            yield ctx.commit()

            app_log.info((sql_01, order_info_dict))
            app_log.info((sql_02, order_product_info_dict))
            app_log.info((sql_03, order_finance_info_dict))
            app_log.info((sql_04, order_invoice_info_dict))
            app_log.info((sql_05, order_contract_info_dict))
            app_log.info((sql_06, order_receive_info_dict))
            app_log.info((sql_07, order_logistics_info_dict))

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
    def update_one_by_dicts(self, _id, param_dict, is_log=False):
        """ update  2017.9.5"""
        order_info_dict = param_dict["order_info_dict"]
        order_product_info_dict = param_dict["order_product_info_dict"]
        order_finance_info_dict = param_dict["order_finance_info_dict"]
        order_invoice_info_dict = param_dict["order_invoice_info_dict"]
        order_contract_info_dict = param_dict["order_contract_info_dict"]
        order_receive_info_dict = param_dict["order_receive_info_dict"]
        order_logistics_info_dict = param_dict["order_logistics_info_dict"]
        # self.filter_param_delimiting(order_info_dict)
        # self.filter_param_delimiting(order_finance_info_dict)
        # self.filter_param_delimiting(order_contract_info_dict)
        # self.filter_param_delimiting(order_logistics_info_dict)
        self.filter_param_delimiting_batch([order_info_dict, order_finance_info_dict, order_contract_info_dict, order_logistics_info_dict])
        sql_01 = self.make_update_sql_by_dict('order_info', _id, order_info_dict)
        sql_02 = self.make_update_sql_by_dict('order_product_info', _id, order_product_info_dict)
        sql_03 = self.make_update_sql_by_dict('order_finance_info', _id, order_finance_info_dict, 'order_id')
        sql_04 = self.make_update_sql_by_dict('order_invoice_info', _id, order_invoice_info_dict, 'order_id')
        sql_05 = self.make_update_sql_by_dict('order_contract_info', _id, order_contract_info_dict, 'order_id')
        sql_06 = self.make_update_sql_by_dict('order_receive_info', _id, order_receive_info_dict, 'order_id')
        sql_07 = self.make_update_sql_by_dict('order_logistics_info', _id, order_logistics_info_dict, 'order_id')


        app_log.info((sql_01, order_info_dict))
        app_log.info((sql_02, order_product_info_dict))
        app_log.info((sql_03, order_finance_info_dict))
        app_log.info((sql_04, order_invoice_info_dict))
        app_log.info((sql_05, order_contract_info_dict))
        app_log.info((sql_06, order_receive_info_dict))
        app_log.info((sql_07, order_logistics_info_dict))


        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield store.execute(sql_01, tuple(order_info_dict.values()))
                yield store.execute(sql_02, tuple(order_product_info_dict.values()))
                yield store.execute(sql_03, tuple(order_finance_info_dict.values()))
                yield store.execute(sql_04, tuple(order_invoice_info_dict.values()))
                yield store.execute(sql_05, tuple(order_contract_info_dict.values()))
                yield store.execute(sql_06, tuple(order_receive_info_dict.values()))
                yield store.execute(sql_07, tuple(order_logistics_info_dict.values()))
                yield ctx.commit()
                flag = True
            except:
                app_log.error("update failed, details: {0}".format(traceback.format_exc()))
                yield ctx.rollback()
                flag = False

        if is_log:
            app_log.info(("update order ?", flag, _id, param_dict))
        raise Return(flag)


    @coroutine
    def delete_more_with_deleted(self, ids, deleted=False, is_log=False):
        """deleted=False假删除，只是改数据库的字段。=True真删除  8.16"""
        if deleted:
            with StoreContext() as store:
                for _id in ids:
                    ctx = yield store.begin()
                    try:
                        yield ctx.execute("""DELETE FROM order_info WHERE _id = %s""", _id)
                        yield ctx.execute("""DELETE FROM order_product_info WHERE _id = %s""", _id)
                        yield ctx.execute("""DELETE FROM order_finance_info WHERE order_id = %s""", _id)
                        yield ctx.execute("""DELETE FROM order_invoice_info WHERE order_id = %s""", _id)
                        yield ctx.execute("""DELETE FROM order_contract_info WHERE order_id = %s""", _id)
                        yield ctx.execute("""DELETE FROM order_receive_info WHERE order_id = %s""", _id)
                        yield ctx.execute("""DELETE FROM order_logistics_info WHERE order_id = %s""", _id)
                        yield ctx.commit()
                        flag = True
                    except:
                        app_log.error("delete order _id={0} failed, details: {1}".format(_id, traceback.format_exc()))
                        yield ctx.rollback()
                        flag = False
        else:
            flag = yield self.batch("""UPDATE order_info SET deleted=1 WHERE _id = %s""", ids)
        if is_log:
            app_log.info(("delete ?", flag, ids))
        raise Return(flag)


order_model = OrderModel()
contract_status_model = OrderContractStatusModel()
order_status_model = OrderStatusModel()