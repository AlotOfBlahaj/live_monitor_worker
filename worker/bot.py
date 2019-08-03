import requests
import json

from tools import get_logger
from config import config
from sub import Subscriber


# 关于机器人HTTP API https://cqhttp.cc/docs/4.7/#/API
def bot(message: str, user: str):
    user_config = config['users'][user]
    if user_config['bot_notice']:
        try:
            group_id = user_config['group_id']
        except KeyError:
            group_id = config['group_id']
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
            logger = get_logger()
            try:
                requests.post(f'http://{config["bot_host"]}/send_group_msg', data=msg, headers=headers)
                logger.warning(f'{msg}')
            except requests.exceptions.RequestException as e:
                logger.exception(e)


def call_bot(video_dict):
    if video_dict['Provide'] == 'Youtube' or 'Twitcasting' or 'Openrec' or 'Mirrativ':
        bot(f"[直播提示] {video_dict['Provide']} {video_dict.get('Title')} 正在直播 链接: {video_dict['Target']} [CQ:at,qq=all]",
            video_dict['User'])
    elif video_dict['Provide'] == 'Bilibili':
        bot(f'[烤肉提示] [Bilibili] {video_dict.get("Title")} 链接: {video_dict.get("Ref")}', video_dict['User'])


def worker():
    sub = Subscriber()
    while True:
        video_dict = sub.do_subscribe()
        call_bot(video_dict)