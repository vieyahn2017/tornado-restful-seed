# Tornado种子项目
## 技术栈
Tornado
数据库Postgresql
缓存Redis


##依赖库：  
tornado   
psycopg2   
redis   
##运行：
>python app.py
  
默认端口9031
按天记录日志log_20161226.log  
***



## 数据同步程序
本程序负责接收客户端发来的数据， 并存入服务器端的目标数据库（postgresql数据库）。

### 配置文件：
config.py  
   
>gpsDataName = 'trajectoryData' #目前只接收gps数据

#### 实时信息推送请求URL      
存入redis消息队列lcic_gps_queue:key  

### 特别说明
（本种子项目，还有部分业务代码，已经部分打乱：   
如数据表名字已经改为b_table，字段已经改成key。）   
不存在泄露业务机密的。
