# -*- coding:utf-8 -*- 
# --------------------
# Author:		gxm1015@qq.com
# Description:	WebServices base model.
# --------------------
import time

from tornado.gen import coroutine, Return
from tornado.log import app_log

from models import BaseModel


class BaseWSModel(BaseModel):
    """
    Base Class for WebServices Model.
    It contains some reusable method.
    Other model in WebServices must inherit from this class.
    """

    def __init__(self):
        super(BaseWSModel, self).__init__()

    @coroutine
    def pay_update_order_state(self, user_id, order_id, order_price):
        """
        支付成功后, 更新订单购买状态
        1.pay order 2. update order state set buy_state = '1' (pay success) else rollback()
        """
        ctx = yield self.begin()
        try:
            pay_result = yield self._pay_order(ctx, user_id, order_price)
            if pay_result <= 0:
                yield ctx.rollback()
                raise Return(-1)
            state_result = yield self._update_state(ctx, order_id)
            if state_result <= 0:
                yield ctx.rollback()
                raise Return(-1)
            yield ctx.commit()
        except Exception as e:
            app_log.error(e)
            import traceback
            print(traceback.print_exc())
            yield ctx.rollback()
            raise Return(-1)
        else:
            raise Return(1)

    @coroutine
    def _pay_order(self, ctx, user_id, order_price):
        """
        订单支付扣费, 返回1成功
        @param ctx: Future[Transaction]
        @param user_id:  user's id
        @param order_price: order price
        """
        if order_price == 0:
            raise Return(1)
        cur = yield ctx.execute(
            "UPDATE sys_user_info "
            "SET money=money-%s "
            "WHERE _id=%s ", (order_price, user_id)
        )
        raise Return(cur.rowcount)

    @coroutine
    def _update_state(self, ctx, order_id):
        """Update the order purchase status"""
        cur = yield ctx.execute(
            "UPDATE webservice_orders "
            "SET buy_state='1' "
            "WHERE _id=%s ", order_id
        )
        raise Return(cur.rowcount)

    @coroutine
    def get_user_host(self, user_id):
        """Get user's cloud host instance list"""
        result = yield self.query(
            "SELECT wom.vm_id, wom.order_id, wom.name, wom.auto_renew, wom.area_id, "
            "wo.buy_month, wo.buy_date, wo.end_date, wo.total_money, wo.buy_state "
            "FROM webservice_orders_machine wom "
            "LEFT JOIN webservice_orders  wo "
            "ON wom.order_id = wo._id "
            "WHERE wom.user_id=%s "
            "AND wom.vm_id != 0 "
            "AND wo.buy_state = '1' "
            "AND wo.end_date > %s "
            "ORDER BY wo.buy_date DESC ",
            (user_id, int(time.time()))
        )
        raise Return(result)

    @staticmethod
    def generate_order_no(user_id, order_type):
        """generate order no"""
        time_str = time.strftime('%Y%m%d%H%M')
        return time_str + str(order_type) + str(user_id)

    @staticmethod
    def get_buy_start_end_time(duration_value, duration_type):
        """
        Calculate order start and end time
        :param: duration_value: int  购买时长
        :param: duration_type: string 购买时长类型: '1'-年 | '2'-月 | '3'-日 | '4'-小时
        """
        # TODO use timedelta
        start = int(time.time())
        duration_type = str(duration_type)
        end = ''
        if duration_type == '1':
            end = start + duration_value * 365 * 24 * 3600
        elif duration_type == '2':
            end = start + duration_value * 30 * 24 * 3600
        elif duration_type == '3':
            end = start + duration_value * 24 * 3600
        elif duration_type == '4':
            end = start + duration_value * 3600
        else:
            raise ValueError('duration value error. {0}'.format("'1'-年 | '2'-月 | '3'-日 | '4'-小时"))
        return start, end
