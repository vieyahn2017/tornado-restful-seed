# -*- coding:utf-8 -*- 
# --------------------
# Author:	yh001
# Description:	
# --------------------
import os.path
import sys
import logging
import time

def compositeLogger(name, level, log_file):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    #logger.addHandler(ch)
    return logger


yearmonth = time.strftime("%Y%m%d", time.localtime())
log_file = os.path.join(os.path.dirname(__file__), 'log_' + yearmonth + '.log')

logger = compositeLogger('mylogger', logging.DEBUG, log_file) 