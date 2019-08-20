import logging
from time import strftime, localtime, time

import pymongo
import re
from bson import ObjectId
from os import mkdir
from os.path import abspath, dirname, isdir, isfile

from config import config

ABSPATH = dirname(abspath(__file__))
fake_headers = {
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0',
}
proxies = {
    "http": f"http://{config['proxy']}",
    "https": f"http://{config['proxy']}",
}


def get_logger():
    if not isdir('log'):
        mkdir('log')
    logger = logging.getLogger('run')
    today = strftime('%m-%d', localtime(time()))
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename=f"log/log-{today}.log")
    formatter = logging.Formatter("%(asctime)s[%(levelname)s]: %(filename)s[line:%(lineno)d] - %(name)s : %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.WARNING)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


class Database:
    def __init__(self, db: str):
        client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
        _db = client["Video"]
        self.db = _db[db]
        self.logger = logging.getLogger('run.db')

    def select(self):
        values = self.db.find()
        return values

    def delete(self, _id):
        self.db.delete_one({"_id": ObjectId(_id)})
        self.logger.info(f"ID: {_id} has been deleted")

    def _insert(self, _dict):
        result = self.db.insert_one(_dict)
        self.logger.info(result)

    def _modify(self, _title, _dict):
        result = self.db.find_one_and_update({"Title": _title}, {'$set': _dict})
        self.logger.info(result)

    def auto_insert(self, _title, _dict):
        result = self.db.find_one({'Title': _title})
        if not result:
            self._insert(_dict)
        else:
            self._modify(_title, _dict)


def check_ddir_is_exist(ddir=config['ddir']):
    if not isdir(ddir):
        try:
            mkdir(ddir)
        except FileNotFoundError:
            logger = logging.getLogger('run.check_ddir')
            logger.exception('下载目录（ddir）配置错误，请选择可用的目录')
            exit(-1)


def get_ddir(user_config):
    try:
        if user_config['ddir'] != config['ddir']:
            ddir = f'{config["ddir"]}/{user_config["ddir"]}'
        else:
            ddir = config['ddir']
    except KeyError:
        ddir = config['ddir']
    return ddir


def get_user(name):
    for user in config['users']:
        if name == user['user']:
            return user
    else:
        raise RuntimeError(f'Can not find {name}')


class AdjustFileName:

    def __init__(self, filename):
        self.filename = filename

    def title_block(self):
        replace_list = ['|', '/', '\\', ':', '?']
        for x in replace_list:
            self.filename = self.filename.replace(x, '#')

    def file_exist(self, ddir):
        i = 0
        paths = f'{ddir}/{self.filename}'
        if isfile(paths):
            while True:
                new_filename = self.filename + f'_{i}'
                if not isfile(f'{ddir}/{new_filename}'):
                    self.filename = new_filename
                    break
                i += 1
        else:
            self.filename = self.filename

    def filename_length_limit(self):
        lens = len(self.filename)
        if lens > 80:
            self.filename = self.filename[:80]

    def remove_emoji(self):
        emoji_pattern = re.compile(
            u'(\U0001F1F2\U0001F1F4)|'  # Macau flag
            u'([\U0001F1E6-\U0001F1FF]{2})|'  # flags
            u'([\U0001F600-\U0001F64F])'  # emoticons
            "+", flags=re.UNICODE)
        self.filename = emoji_pattern.sub('', self.filename)

    def adjust(self, ddir):
        self.remove_emoji()
        self.title_block()
        self.filename_length_limit()
        self.file_exist(ddir)
        return self.filename
