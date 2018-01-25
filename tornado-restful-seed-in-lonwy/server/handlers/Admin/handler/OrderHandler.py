# -*- coding:utf-8 -*- 
# --------------------
# Author:		gxm1015@qq.com
# Create:  2017/6/29 下午3:50
# Description:	
# --------------------
from tornado import escape
from tornado.gen import coroutine
from tornado.log import app_log

from handlers import Route
from handlers import BaseADHandler
from ..model.OrderModel import order_model, order_status_model, contract_status_model
from ..model.ProductModel import product_model



@Route(r'admin/order/status')
class OrderStutasHandler(BaseADHandler):

    @coroutine
    def get(self, *args):
        items = yield order_status_model.get_all()
        self.write_rows(rows=items)


@Route(r'admin/order/contract/status')
class OrderContractStutasHandler(BaseADHandler):

    @coroutine
    def get(self, *args):
        items = yield contract_status_model.get_all()
        self.write_rows(rows=items)



@Route(r'admin/order')
@Route(r'admin/order/(\d+)')
class OrderMainHandler(BaseADHandler):

    @coroutine
    def get(self, *args):

        is_log = False #True
        if args:
            _id = args[0]
            item = yield order_model.get_one(_id, is_log=is_log)
            product_id = item["product_id"]
            if product_id:
                item_product_addon = yield product_model.get_one_for_order(product_id)
                item.update(item_product_addon)
            self.write_rows(rows={"order": item})

        else:
            order_no = self.get_argument('order_no', '')
            if order_no != '':
                result = yield order_model.get_by_order_no(order_no)
                self.write_rows(rows={'orderList': result, 'count': 1})
            else:
                product_type_id = self.get_argument('product_type_id', '')
                product_category_id = self.get_argument('product_category_id', '')
                order_status_id = self.get_argument('order_status_id', '')
                finance_charge_status_id = self.get_argument('finance_charge_status_id', '')
                param_dict = {
                    'page_no': int(self.get_argument('page_no', 1)),
                    'page_size': int(self.get_argument('page_size', 10)),
                    'product_type_id': int(product_type_id) if product_type_id else 0,
                    'product_category_id': int(product_category_id) if product_category_id else 0,
                    'order_status_id': int(order_status_id) if order_status_id else 0, 
                    'finance_charge_status_id': int(finance_charge_status_id) if finance_charge_status_id else 0, 
                }
                result, count = yield order_model.get_all(**param_dict)
                self.write_rows(rows={'orderList': result, 'count': count})


    @coroutine
    def post(self):
        """
        :新增订单 
        """
        param_dict = escape.json_decode(self.request.body)
        # if not self.is_param_valid(param_dict):
        #     self.write_rows(code=1, msg='Param can not be empty')
        #     return
        result = yield order_model.add_order(param_dict)
        if result > 1:
            self.write_rows(rows=result, msg='succeed')
        elif result == -1:
            self.write_rows(code=-1, msg='Insert db error')
        elif result == -2:
            self.write_rows(code=-1, msg='Missing argument')


    @coroutine
    def put(self):
        is_log = True
        param_dict = escape.json_decode(self.request.body)
        if is_log:
            app_log.info(param_dict)
        # if not self.is_param_valid(param_dict):
        #     self.write_rows(code=-1, msg='Param can not be empty')
        #     return # 非空校验

        _id = param_dict["_id"]

        flag = yield order_model.update_one_by_dicts(_id, param_dict, is_log=is_log)
        code = 1 if flag else -1
        self.write_rows(code=code)


    @coroutine
    def delete(self, *args):
        """
        if: 删除一条:  http://10.0.0.161:30082/api/v1/admin/order/6
        else:批量删除: http://10.0.0.161:30082/api/v1/admin/order?ids=2,6
        """
        if args:
            ids = [args[0], ]
        else:
            ids_str = self.get_argument('ids', '0').encode('utf-8')
            ids = filter(str.isdigit, ids_str.split(','))

        is_log = True
        flag = yield order_model.delete_more_with_deleted(ids, is_log=is_log)

        code = 1 if flag else -1
        self.write_rows(code=code)
