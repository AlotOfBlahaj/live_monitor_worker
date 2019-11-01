import json
from datetime import datetime

import requests

from config import config
from pubsub import Subscriber
from tools import get_logger, get_user

logger = get_logger()
last_at = None


# 关于机器人HTTP API https://cqhttp.cc/docs/4.7/#/API
def bot(message: str, bot_config: dict):
    # 传入JSON时，应使用这个UA
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Bearer {bot_config["bot_token"]}'}
    for _group_id in bot_config['group_id']:
        _msg = {
            'group_id': int(_group_id),
            'message': message,
            'auto_escape': False
        }
        msg = json.dumps(_msg)
        try:
            r = requests.post(f'http://{bot_config["bot_host"]}/send_group_msg', data=msg, headers=headers)
            logger.warning(f'send {_msg}')
            logger.warning(r.text)
        except requests.exceptions.RequestException as e:
            logger.exception(e)


def call_bot(video_dict: dict) -> None:
    user_config = get_user(video_dict['User'])
    if user_config['bot_notice']:
        bot_config = dict()
        config_item = ['group_id', 'bot_host', 'bot_token']
        for item in config_item:
            if item in user_config:
                bot_config[item] = user_config[item]
            else:
                bot_config[item] = config[item]
        msg = filter_at(video_dict['User'], video_dict['Msg'])
        bot(msg, bot_config)


def filter_at(user, msg: str):
    if '[CQ:at,qq=all]' not in msg:
        return msg
    global last_at
    if last_at is None:
        last_at = (user, datetime.now())
        return msg
    else:
        now_time = datetime.now()
        if last_at[0] != user:
            set_last_at(user, now_time)
            return msg
        timedelta = now_time - last_at[1]
        sec_delta = timedelta.seconds
        if sec_delta <= 120:
            msg = msg.replace('[CQ:at,qq=all]', '')
        set_last_at(user, now_time)
        return msg


def set_last_at(user, at_time):
    global last_at
    last_at = (user, at_time)


def worker() -> None:
    sub = Subscriber(('main', 'bot'))
    logger.info('Bot worker is already running')
    while True:
        video_dict = sub.do_subscribe()
        if 'Msg' in video_dict:
            call_bot(video_dict)


if __name__ == '__main__':
    worker()
