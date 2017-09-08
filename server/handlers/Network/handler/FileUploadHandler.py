# -*- coding:utf-8 -*- 
# --------------------
# Author:		gxm1015@qq.com
# Description:
# --------------------
import hashlib
import os
import random
import time

from PIL import Image
from PIL import ImageFile
from tornado.log import app_log
from tornado.web import HTTPError

from handlers import Route
from config import UPLOAD_TEMP_PATH, UPLOAD_URL, VALID_FILE_EXT
from config import FILE_UPLOAD_PATH, TEMP_UPLOAD_PATH
from handlers import BaseADHandler

ImageFile.LOAD_TRUNCATED_IMAGES = True


@Route(r'webservices/upload')
class UploadHandler(BaseADHandler):
    def get(self):
        self.write('''
            <html>
              <head><title>Upload File</title></head>
              <body>
                <form action='/api/v1/webservices/upload' enctype="multipart/form-data" method='post'>
                <input type='file' name='file'/><br/>
                <input type='submit' value='submit'/>
                </form>
              </body>
            </html>
    ''')

    def post(self, *args, **kwargs):
        box = self.get_argument('box', None)
        size = int(self.request.headers.get('Content-Length'))
        if size / 1000.0 > 2000:
            self.set_status(400)
            self.write({'msg': u"上传图片不能大于2M."})
            return
        file_info = self.request.files['file'][0]
        file_name = self.generate_file_name(file_info['filename'])
        if not file_name:
            self.write_rows(code=-1, msg='Invalid file name')
            return
        year_month, day = time.strftime("%Y%m"), time.strftime("%d")
        path = os.path.join(FILE_UPLOAD_PATH, year_month, day)
        temp_path = os.path.join(TEMP_UPLOAD_PATH, file_name)
        absolute_path = os.path.join(path, file_name)
        app_path = absolute_path[absolute_path.rindex('upload'):]
        self.create_dir(path)
        try:
            with open(temp_path, 'wb') as f:
                f.write(file_info['body'])
                if box:
                    self.crop_image(temp_path, box)
                self.write_rows(rows={
                    'path': absolute_path,
                    'app_path': app_path,
                    'temp_path': temp_path
                })
        except Exception as e:
            app_log.error(e)
            raise HTTPError(500)

    @staticmethod
    def create_dir(path):
        """创建图片存储目录"""
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                app_log.error(e)
                raise HTTPError(500)

    @staticmethod
    def generate_file_name(file_name):
        """
        生成文件名
        :param file_name
        """
        f, ext = os.path.splitext(file_name)
        if ext not in VALID_FILE_EXT:
            return None
        else:
            return hashlib.md5(str(time.time())).hexdigest() + str(random.randint(1, 100)) + ext

    @staticmethod
    def create_thumbnail(infile, size):
        """
        生成缩略图
        :param infile: 需要生外理图片的绝对路径
        :param size: 缩略图尺寸 size =（x, y）
        :return success return file_path else None  (*_x_y.ext)
        """
        f, ext = os.path.splitext(infile)
        file_path = f + '_' + str(size[0]) + '_' + str(size[1]) + ext
        try:
            img = Image.open(infile)
            img.thumbnail(size, Image.ANTIALIAS)
            img.save(file_path, 'JPEG')
            return file_path
        except Exception as e:
            app_log.error(e)

    @staticmethod
    def crop_image(infile, box):
        """
        裁剪图片
        :param infile: 图片绝对路径
        :param box: 裁剪范围 box =（a, b, c, d）客户端传入
        :return: success return infile else None
        """
        try:
            img = Image.open(infile)
            region = img.crop(box)
            region = region.transpose(Image.ROTATE_180)
            region.save(infile)
        except Exception as e:
            app_log.error(e)
