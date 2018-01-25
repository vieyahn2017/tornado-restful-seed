# -*- coding:utf-8 -*- 
# --------------------
# Author:	yh001
# Description:	
# --------------------

import json
import re
import time
import datetime

from tornado.escape import json_encode
from tornado.httpclient import AsyncHTTPClient

from config import VEHICLE_TYPE, SYNC_TYPE, GPS_QUEUE_KEY
from log.mylogger import logger as mylogger
from db.dbManager import rsdb
from db.dbManager import pgconn as connection
cursor = connection.cursor()

log_details_true = False # True #  每次写入成功，都详细记录


def parse_time2str(cs_json_time):
    """  格式化时间
    json获取的格式是 /Date(1480349734000)/ 
    这是C#的JavaScriptSerializer封装的格式
    """
    try:
        time_secs = int(re.sub('\D', '', cs_json_time)[:-3]) + datetime.timedelta(hours=8).total_seconds()
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time_secs))
    except Exception, e:
        return "1970-01-01 01:01:01"
        #2017.2.22罕见的接收了一个/Date(0)/，报错，所以增加try except



def set_alarm_type(alarm_type):
    """ 把这个映射改在c#那边吧 """
    try:
        from config import alarmTypeDict
        return alarmTypeDict[alarm_type]
    except Exception, e:
        #print repr(e)
        return 0

def is_empty(empty):
    """pg里面 'yes' 'no' 可以作为布尔判断的取值"""    
    return empty


def is_validate(pos_invalidate):
    if pos_invalidate == 0:
        return "false"
    else:
        return "true"

def parse_point(pt_str):
    return 'ST_GeomFromText(%s, 4326)' % pt_str


def push_gps_json_to_redis(action_type, **item):
    """推送到redis 车辆GPS实时信息队列"""
    location_json = json_encode(
        {
            "type": "",
            "action": action_type,
            "data": {
                "vehicle_card": item["taxiNo"],
                "lng": float(item["lng"]),
                "lat":  float(item["lat"]),
                "direction": float(item["direction"]),
                "speed": float(item["speed"]) 
            }

        }
    )
    rsdb.lpush(GPS_QUEUE_KEY, location_json)
    if log_details_true:
        mylogger.info("[redis push:] {0}".format(location_json))


def get_vehicle_gps_json(action_type, **item):
    """
    返回车辆当定位相关信息, 用于POST到LCIC 相关的PublishHandler
    location_json:
    {
        "action": "update", 
        "data": {"lat": 30.645, "vehicle_card": "\u82cfAD4978", "lng": 104.0328, "speed": 15.433333333333334, "direction": 270.001}, 
        "type": "taxi"
    }
    """
    type_id = item['vehicle_type']
    location_json = json.dumps(
        {
            "type": VEHICLE_TYPE[type_id],
            "action": action_type,
            "data": {
                "vehicle_card": item["taxiNo"],
                "lng": float(item["lng"]),
                "lat":  float(item["lat"]),
                "direction": float(item["direction"]),
                "speed": float(item["speed"])  
            }
        }
    )
    return location_json


def car_real_location_to_db(**item):
    """ 将所有接收的gps信息写入总表 here_is_db_table """

    _sql =  """INSERT INTO "here_is_db_table" (key, key, key, key, time, key, is_empty, is_validate, pt)
               VALUES ('{0}',{1},{2},{3},'{4}','{5}','{6}','{7}',ST_GeomFromText('{8}', 4326))""".format(
                 item['key'], SYNC_TYPE['key'], int(item['key']), int(item['key']), parse_time2str(item['time'])
                , item['key'], item['empty'], is_validate(item['key']), item['pt'])


    if log_details_true:
        mylogger.info("[insert GPS datas] {0}".format(_sql))

    try:        
        cursor.execute(_sql )    
        connection.commit()

    except Exception, e:
        connection.rollback()
        mylogger.error("db Error -{0}- when insert sql---: {1}".format(e, _sql) ) 


def query_vehicle_propertyid(VehId):
    """查询VehId的车辆的vehiclepropertyid"""

    get_sql = "SELECT key FROM db_table where vehicle_card ='{0}' ".format(VehId)
    try:
        cursor.execute(get_sql) 
        result = cursor.fetchone()  #tuple
    except Exception, e:
        mylogger.error("db Error - %s: "% e) 

    #print 'type for sql: ', result

    if result is not None:
        return result[0]
    else:
        return 3


def query_vehicle_is_exist(vehId):
    """查询VehId的车辆，是否在当前位置信息表里"""

    query_sql = "select 1 from here_is_db_table where vehicle_card = '%s'" % vehId
    result = False
    try:
        cursor.execute(query_sql) 
        if cursor.fetchone() is not None:
            result = True
    except Exception, e:
        mylogger.error("db Error - %s - when query vehicle_card exist from db" % e) 

    return result


def update_dt_vehicle_gps(**item):
    """
    更新车辆当前位置信息
    item:
    {u'direction': 270.001, u'posInvalidate': 0, 'pt': 'POINT(104.0328 30.645)', 
    u'taxiNo': u'\u4eacA33333', u'empty': u'yes', u'time': u'/Date(1487317354000)/', 
    u'lat': 30.645, u'lng': 104.0328, 'vehicle_type': 3, u'speed': 15.433333333333334, u'alarmType': 0}

    """
    #print item

    action_type = "update"
    time_str = parse_time2str(item['time'])

    update_sql = "UPDATE here_is_db_table SET pt=ST_GeomFromText('{0}', 4326), is_empty='{1}', key={2}, key={3}, time='{4}', key={5} WHERE vehicle_card = '{6}'".format(
            item['pt'], item['key'], int(item['key']), int(item['key']), time_str, item['key'], item['taxiNo'])

    try:
        cursor.execute(update_sql)
        connection.commit()
        if log_details_true:
            mylogger.info("[update gps data] {0}" .format(update_sql))

    except Exception, e:
        connection.rollback()
        mylogger.error("db Error -{0}- when update, sql---: {1}".format(e, update_sql) )
    
    else:
        push_gps_json_to_redis(action_type, **item)


def insert_dt_vehicle_gps(**item):
    """ 向here_is_db_table 插入新数据"""
    action_type = "insert"
    time_str = parse_time2str(item['time'])

    insert_sql = """INSERT INTO "here_is_db_table" (key, sync_type, key, key, time, alarm_type, is_empty, pt) VALUES ('{0}',{1},{2},{3},'{4}','{5}','{6}',ST_GeomFromText('{7}', 4326))""".format(
          item['taxiNo'], SYNC_TYPE['weijie'], int(item['key']), int(item['key']), time_str, item['alarmType'], item['empty'], item['pt'])

    try:
        cursor.execute(insert_sql)
        connection.commit()
        if log_details_true:
            mylogger.info("[insert gps data] {0}".format(insert_sql))

    except Exception, e:
        connection.rollback()
        mylogger.error("db Error -{0}- when insert, sql---: {1}".format(e, insert_sql) )
 
    else:
        push_gps_json_to_redis(action_type, **item)