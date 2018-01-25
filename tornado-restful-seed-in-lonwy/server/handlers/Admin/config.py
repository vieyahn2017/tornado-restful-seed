# -*- coding:utf-8 -*- 
# --------------------
# Author:       gxm1015@qq.com
# Description:  Some conf for Webservice module
# --------------------



# 删除模式 1 - 严格模式, 将执行真实删除操作 0 - 仅逻辑上删除.
DELETE_MODE = 0

TICKETS_TYPE = {
    'suggest_type': 2,
    'work_order_type': 1
}

# 购买时长类型
DURATION_TYPE = {
    '1': u'年',
    '2': u'月',
    '3': u'日',
    '4': u'小时'
}



import os.path
from tornado.log import app_log

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FILE_UPLOAD_PATH = os.path.join(BASE_DIR, "upload")  # 文件上传目录
TEMP_UPLOAD_PATH = os.path.join(FILE_UPLOAD_PATH, "temp")  # 临时文件目录
if not os.path.exists(TEMP_UPLOAD_PATH):
    try:
        os.makedirs(TEMP_UPLOAD_PATH)
    except Exception as e:
        app_log.error(e)

if not os.path.exists(FILE_UPLOAD_PATH):
    try:
        os.makedirs(FILE_UPLOAD_PATH)
    except Exception as e:
        app_log.error(e)

# Used for generate email confirm token.
TOKEN_SECRET = 'L\xb0!\xfdi\xea\x8b\xce{\xc9\x14#ta\x1c\xef'

# sms code effective duration
VERIFY_CODE_EXPIRE = 120

# email code effective duration
EMAIL_CODE_EXPIRE = 600

# CACHE KEY
WS_CACHE_KEY = 'webservice_cache:query:{0}'
WS_REQ_CACHE_KEY = 'webservice_cache:request:{0}'

# CACHE EXPIRE
MINUTE = 60
HALF_HOUR = 60 * 30
HOUR = 60 * 60
HALF_DAY = 60 * 60 * 12
DAY = 60 * 60 * 24

# Order type map
ORDER_TYPE = {
    1: 'buy_cloud_host',
    2: 'buy_network',
    3: 'buy_cloud_disk'
}

ORDER_TYPE_REVERSE = {
    'buy_cloud_host': 1,
    'buy_network': 2,
    'buy_cloud_disk': 3
}

# 购买时长类型
DURATION_TYPE = {
    '1': u'年',
    '2': u'月',
    '3': u'日',
    '4': u'小时'
}

DURATION_TYPE_MAP = {
    '1': 'year_price',
    '2': 'month_price',
    '3': 'day_price',
    '4': 'hour_price'
}

