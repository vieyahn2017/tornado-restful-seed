# -*- coding: utf-8 -*- 
# --------------------
# Author:	yh001
# Description:	
# --------------------

import sys
import json
from tornado.web import RequestHandler
from log.mylogger import logger
from config import gpsDataName
from db import model

class TaxGpsCollectorHandler(RequestHandler):

	def get(self):
		self.write("get success! but this Application work with POST method.")

	def post(self):
		# db Error: 'ascii' codec can't encode character u'\u5ddd' in position 101: ordinal not in range(128)
		reload(sys)
		sys.setdefaultencoding('utf-8')

		url_type = self.get_argument('type')
		if url_type == gpsDataName:
			
			data = self.get_body_argument(gpsDataName)
			datas = json.loads(data)
			logger.info("===== load  %s items :  %s" % (gpsDataName, len(datas)) )	

			for item in datas:
				item["pt"] = 'POINT({0} {1})'.format(item['lng'], item['lat'])
				model.car_real_location_to_db(**item)

				exist = model.query_vehicle_is_exist(item['taxiNo'])
				if exist:
					model.update_dt_vehicle_gps(**item)
				else:
					model.insert_dt_vehicle_gps(**item)


		elif url_type == "serviceData":
			print " Module for serviceData === todo"
			pass






