# -*- coding:utf-8 -*- 
# --------------------
# Author:		gxm1015@qq.com
# Create:  2017/6/23 上午10:59
# Description:	
# --------------------

from itsdangerous import SignatureExpired, BadSignature
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tornado.log import app_log

from config import TOKEN_SECRET


def generate_auth_token(data, expiration=7200):
    """生成access token用于用户认证, 默认有效期2小时"""
    s = Serializer(TOKEN_SECRET, expires_in=expiration)
    return s.dumps(data).decode('utf-8')


def verify_auth_token(token):
    """验证access token有效性"""
    s = Serializer(TOKEN_SECRET)
    try:
        data = s.loads(token)
    except SignatureExpired as e:
        app_log.error('Signature expired: {0}'.format(e))
        return -1
    except BadSignature as e:
        app_log.error('Bad signature: {0}'.format(e))
        return -2
    else:
        return data
