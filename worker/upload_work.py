import logging
import re
import subprocess
from abc import ABCMeta, abstractmethod
from datetime import datetime
from os import name
from threading import Thread, Lock
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError
from retrying import retry

from config import config
from pubsub import Subscriber, Publisher
from tools import get_logger, ABSPATH, Database, get_user

logger = get_logger()


class Upload(metaclass=ABCMeta):
    @abstractmethod
    def upload_item(self, item_path: str, item_name: str) -> None:
        pass


class S3Upload(Upload):
    def __init__(self) -> None:
        self.logger = logging.getLogger('run.s3upload')
        self.s3_client = boto3.client('s3',
                                      endpoint_url=config['s3_server'],
                                      aws_access_key_id=config['s3_access_key'],
                                      aws_secret_access_key=config['s3_secret_key'])

    def upload_item(self, item_path: str, item_name: str) -> bool:
        try:
            self.s3_client.upload_file(item_path, config['s3_bucket'], item_name)
            return True
        except ClientError as e:
            self.logger.error(e)
            raise RuntimeError('Upload error')


class BDUpload(Upload):
    def __init__(self) -> None:
        self.logger = logging.getLogger('run.bdupload')

    @retry(stop_max_attempt_number=3)
    def upload_item(self, item_path: str, item_name: str) -> bool:
        if 'nt' in name:
            command = [f"{ABSPATH}\\BaiduPCS-Go\\BaiduPCS-Go.exe", "upload"]
        else:
            command = [f"{ABSPATH}/BaiduPCS-Go/BaiduPCS-Go", "upload"]
        command.append(item_path)
        command.append("/")
        bd_lock = Lock()
        with bd_lock:
            p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               encoding='utf-8', universal_newlines=True)
        result = p.stdout
        logger.warning(result)
        if '全部上传完毕' in result:
            return True
        else:
            raise RuntimeError('Upload error')

    @retry(stop_max_attempt_number=3)
    def share_item(self, item_name: str) -> str:
        if 'nt' in name:
            command = [f'{ABSPATH}\\BaiduPCS-GO\\BaiduPCS-Go.exe', "share", "set"]
        else:
            command = [f"{ABSPATH}/BaiduPCS-Go/BaiduPCS-Go", "share", "set"]
        command.append(item_name)
        s2 = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            encoding='utf-8', universal_newlines=True)
        share_info = s2.stdout
        if 'https' in share_info:
            share_info = share_info.replace('\n', '')
            self.logger.info(f'{item_name}: Share successful {share_info}')
        else:
            self.logger.error('Share failed')
            raise RuntimeError(f'{item_name} share failed')
        reg = r'https://pan.baidu.com/s/([A-Za-z0-9_-]{23})'
        linkre = re.compile(reg)
        link = re.search(linkre, share_info)
        try:
            link = 'https://pan.baidu.com/s/' + link.group(1)
            return link
        except AttributeError:
            self.logger.exception('get share link error')
            raise RuntimeError('get share link error')


def upload_video(upload_dict: dict) -> None:
    upload_way_dict = {'bd': BDUpload,
                       's3': S3Upload}
    upload_way = upload_way_dict.get(config['upload_by'])
    uploader = upload_way()
    user_config = get_user(upload_dict['User'])
    result = uploader.upload_item(f"{upload_dict['Path']}", upload_dict['Title'])
    if not result:
        raise RuntimeError('Upload error')
    if config['upload_by'] == 'bd':
        share_url = uploader.share_item(upload_dict['Title'])
        if config['enable_mongodb']:
            data = {"Title": upload_dict['Origin_Title'],
                    "Date": upload_dict['Date'],
                    "Link": share_url,
                    "ASS": upload_dict['ASS']}
            insert_video(upload_dict['User'], data)
    elif config['upload_by'] == 's3':
        if config['enable_mongodb']:
            share_url = f"api/s3?title={quote(upload_dict['Title'])}"
            data = {"Title": upload_dict['Origin_Title'],
                    "Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Link": share_url,
                    "ASS": upload_dict['ASS']}
            insert_video(upload_dict['User'], data)
    else:
        raise RuntimeError(f'Upload {upload_dict["Title"]} failed')
    pub = Publisher()
    data = {'Msg': f"[下载提示] {upload_dict['Title']} 已上传, 请查看https://matsuri.design/",
            'User': user_config['user']}
    pub.do_publish(data, 'bot')


def upload_record(upload_dict: dict) -> None:
    user_config = get_user(upload_dict['User'])
    uploader = BDUpload()
    result = uploader.upload_item(upload_dict['Path'], upload_dict['Title'])
    if not result:
        raise RuntimeError('Upload error')
    if config['upload_by'] == 'bd':
        share_url = uploader.share_item(upload_dict['Title'])
        if config['enable_mongodb']:
            data = {"Title": upload_dict['Origin_Title'],
                    "Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Record": share_url}
            insert_video(upload_dict['User'], data)
            pub = Publisher()
            data = {'Msg': f"[同传提示] {upload_dict['Title']} 已记录, 请查看https://matsuri.design/",
                    'User': user_config['user']}
            pub.do_publish(data, 'bot')


def insert_video(collection: str, data: dict):
    db = Database(collection)
    db.auto_insert(data['Title'], data)


def worker() -> None:
    sub = Subscriber(('upload',))
    while True:
        upload_dict = sub.do_subscribe()
        if upload_dict is not False:
            if upload_dict.get('Record', False):
                t = Thread(target=upload_record, args=(upload_dict,), daemon=True)
            else:
                t = Thread(target=upload_video, args=(upload_dict,), daemon=True)
            t.start()


if __name__ == '__main__':
    worker()
