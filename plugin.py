#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import os
import sublime, sublime_plugin
from .libs.upyun import UpYun, ED_AUTO
import hashlib
from .local_settings import *


def upload_file(bucket_name, folder_path, filename, fp):
    """
    bucket_name: 空间名称
    folder_path: 子目录的绝对路径，比如/wenyouxi/，默认为/（即不使用子目录）
    filename: 需要存在子目录下的文件名，比如tmp.db
    fp: 文件指针，需要用rb模式打开
    """
    u = UpYun(bucket_name, OPERATOR_NAME, OPERATOR_PASSWORD, endpoint=ED_AUTO)

    try:
        # create folder
        u.mkdir(folder_path)
    except:
        pass

    upload_path = os.path.join(folder_path, filename)

    u.put(upload_path, fp, checksum=True)

    return u.getinfo(upload_path), upload_path


class AsyncUploadThread(threading.Thread):
    def __init__(self, filepath, callback):
        self.filepath = filepath
        self.callback = callback
        self.result = None
        threading.Thread.__init__(self)

    def run(self):
        if not self.filepath:
            return self.callback(None)
        try:
            filename, file_ext = os.path.splitext(os.path.basename(self.filepath))
            upload_filename = ''.join([hashlib.sha1(self.filepath.encode('utf8')).hexdigest(), file_ext])
            with open(self.filepath, 'rb') as fp:
                info, url = upload_file(UPYUN_BUCKET, '/upload/', upload_filename, fp)

            if info:
                return self.callback(url)
            else:
                return self.callback(None)
        except Exception as e:
            print(e)
            return self.callback(None)


# Extends TextCommand so that run() receives a View to modify.
class UploadUpyunCommand(sublime_plugin.TextCommand):

    @staticmethod
    def async_upload_callback(result):
        if result:
            sublime.message_dialog(''.join(['File upload success: ',
                                            'http://{bucket}.b0.upaiyun.com'.format(bucket=UPYUN_BUCKET), result]))
        else:
            sublime.message_dialog('Upload failed, please retry.')

    def run(self, edit):
        sublime.status_message('Uploading file to UPYUN...')
        filepath = self.view.file_name()
        new_thread = AsyncUploadThread(filepath=filepath, callback=self.async_upload_callback)
        new_thread.start()

