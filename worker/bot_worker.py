import json
from datetime import datetime

import requests

from config import config
from pubsub import Subscriber
from tools import get_logger, get_user

logger = get_logger()
last_at = None


# 关于机器人HTTP API https://cqhttp.cc/docs/4.7/#/API
def bot(message: str, group_id: tuple):
    # 传入JSON时，应使用这个UA
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Bearer {config["bot_token"]}'}
    for _group_id in group_id:
        _msg = {
            'group_id': int(_group_id),
            'message': message,
            'auto_escape': False
        }
        msg = json.dumps(_msg)
        try:
            requests.post(f'http://{config["bot_host"]}/send_group_msg', data=msg, headers=headers)
            logger.warning(f'send {_msg}')
        except requests.exceptions.RequestException as e:
            logger.exception(e)


def call_bot(video_dict: dict) -> None:
    user_config = get_user(video_dict['User'])
    if user_config['bot_notice']:
        try:
            group_id = user_config['group_id']
        except KeyError:
            group_id = config['group_id']
        msg = filter_at(video_dict['User'], video_dict['Msg'])
        bot(msg, group_id)


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
