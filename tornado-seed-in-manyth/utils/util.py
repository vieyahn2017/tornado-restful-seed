# -*- coding: utf-8 -*- 

import time
import datetime

import random



def getnow(delta=0):
	"""
	目前delta简单处理，int类型，单位秒
	todo:
	    delta: 同mssql的dateadd
			SELECT DateAdd(m,1,GETDATE())
			-- 年 Year yy
			-- 季度 Quarter q
			-- 月 Month m
			-- 周 Week wk
			-- 日 Day d
			-- 小时 Hour hh
			-- 分钟 Minute mi
			-- 秒 Second s
			-- 毫秒Millisecond ms

	timedelta([days[, seconds[, microseconds[, milliseconds[, minutes[, hours[, weeks]]]]]]])
	"""
	tnow = datetime.datetime.now()
	if delta:
		return (tnow + datetime.timedelta(seconds=delta)).strftime('%Y-%m-%d %H:%M:%S')
	return tnow.strftime('%Y-%m-%d %H:%M:%S')

def random4pos():
	while True:
		yield random.uniform(26.20, 27.15), random.uniform(105.98, 107.09), random.randint(0, 360), random.randint(0, 100)


def _test_random4pos(a, b, c, d):
	print a, b, c, d





if __name__ == "__main__":

	print getnow(300)
	print random4pos().next()
	_test_random4pos(*random4pos().next())



