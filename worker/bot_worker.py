import json

import requests

from config import config
from pubsub import Subscriber
from tools import get_logger, get_user

logger = get_logger()


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
        bot(video_dict['Msg'], group_id)


def worker() -> None:
    sub = Subscriber(('main', 'bot'))
    logger.info('Bot worker is already running')
    while True:
        video_dict = sub.do_subscribe()
        if 'Msg' in video_dict:
            call_bot(video_dict)


if __name__ == '__main__':
    worker()
