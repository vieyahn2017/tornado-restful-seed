# -*- coding: utf-8 -*- 
# --------------------
# Author:   yh001
# Description:  
# --------------------

############################
# postgresql 连接参数      #
############################
db_settings = {}
db_settings['POSTGRES_SERVER'] = 'localhost'
db_settings['POSTGRES_PORT'] = 5432
db_settings['POSTGRES_USER'] = 'test'
db_settings['POSTGRES_PW'] = 'test'
db_settings['POSTGRES_DB'] = 'test'
# 这边为了发布到github，因此把用户名密码数据库都改过了，所以直接运行程序会在这里报错


############################
# redis 连接参数           #
############################
REDIS_URL = 'redis://@127.0.0.1:6379'

##### redis 车辆GPS实时信息队列KEY######
GPS_QUEUE_KEY = "lcic_gps_queue:key"

############################
# 同步程序接收参数         #
############################
gpsDataName = 'trajectoryData'



###########################
# 车辆类型映射字典        #
###########################
VEHICLE_TYPE = {
    1: "some_vehicle",  
    2: "another_vehicle", 
    3: "taxi",  # 出租车
}

###
# 同步程序类型

SYNC_TYPE = {
    "weijie": 1,
    "jt809": 2,
    "jiapei": 3,
}