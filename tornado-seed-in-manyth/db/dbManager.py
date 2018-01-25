# -*- coding:utf-8 -*- 
# --------------------
# Author:    yh001
# Description:
# --------------------

import re
import psycopg2
from redis import StrictRedis
from config import REDIS_URL
from config import db_settings
from utils import tornpg

class DbManager(object):
    pass


class PgManager(object):
    def __init__(self):
        self.connection = psycopg2.connect(
                database=db_settings['POSTGRES_DB'],
                user=db_settings['POSTGRES_USER'],
                password=db_settings['POSTGRES_PW'],
                host=db_settings['POSTGRES_SERVER'],
                port=db_settings['POSTGRES_PORT'],
            )

    def makesql(self, db_table, kwargs):
        """ 
        makesql(db_table, **{'speed': '=', 'time': '@parse_time2str', 'is_empty': 'empty@is_empty', 'vehicle_card': 'taxiNo', })
        json解析的item字段和数据库字段，依次为：相同字段，相同字段但是需要加函数处理，不同字段且加函数处理，不同字段


        使用例子如下：

        ins_pre,  ins_lists = makesql('db_table_name', {'vehicle_card' : 'taxiNo', 
                            'vehicle_type' : 'taxiNo@set_vehicle_type', #传输的数据没这个，随便给个参数
                            'lat' : '=', #'lat' : 'lat', 
                            'lng' : '=', 
                            'direction' : '=', 
                            'speed' : '=',
                            'time': '@parse_time2str', # 'time': 'time@parse_time2str',  # 相同的可以省略
                            'alarm_type': 'alarmType', #改在C#那边转换好了，以前的写法不用了 #'alarmType@set_alarm_type', 
                            'is_empty': 'empty@is_empty',
                            })

        insert_sql = ins_pre % tuple(map(lambda x: "'" + str(x) + "'", map(eval, ins_lists)))
        """

        insert = "INSERT INTO %s (" % db_table
        sql_keys = re.sub('[\[\]\'"]', '', str(kwargs.keys()))
        total_s = '%s,' * len(kwargs)
        result_str = insert + sql_keys  + ') VALUES (' + total_s[:-1] + ');'
        all_args_list = []
        for (k, v)  in kwargs.items():
            if v == '=':
                all_args_list.append("item['" + k + "']")
            elif v.startswith('@'):
                all_args_list.append(v[1:] + "(item['" + k + "'])")
            elif '@' in v:
                pv, fn = v.split('@')
                all_args_list.append(fn + "(item['" + pv + "'])")
            else:
                all_args_list.append("item['" + v + "']")

        return result_str, all_args_list

mg = PgManager()
makesql = mg.makesql
pgconn = mg.connection


class RedisManager(object):
    def __init__(self):
        self.redis = StrictRedis.from_url(REDIS_URL)


redisManger = RedisManager()
rsdb = redisManger.redis
