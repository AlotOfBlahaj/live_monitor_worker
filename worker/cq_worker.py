import asyncio
import json
from datetime import datetime

import websockets

from config import config
from pubsub import Subscriber, Publisher
from tools import get_logger, AdjustFileName, get_user, get_ddir

logger = get_logger()


class CQWorker:
    def __init__(self, video_dict: dict) -> None:
        self.video_dict = video_dict
        self.end_sub = Subscriber(('cq',))

    @staticmethod
    def formatter(event_info: dict) -> dict:
        def time_formatter() -> str:
            time_obj = datetime.fromtimestamp(raw_time)
            struct_time = datetime.strftime(time_obj, '%Y年%m月%d日%H:%M:%S')
            return struct_time

        msg = event_info['message']
        raw_time = event_info['time']
        time = time_formatter()
        struct_event_info = {
            'msg': msg,
            'time': time
        }
        return struct_event_info

    def txt_recorder(self, event_info: dict):
        with open(f'{config["ddir"]}/{self.video_dict["Title"]}', 'a') as f:
            f.write(f"{event_info['time']}: {event_info['msg']} \n")
        logger.warning(f"{event_info['time']}: {event_info['msg']}")

    async def ws_interaction(self) -> None:
        while True:
            try:
                async with websockets.connect(config['cq_ws_uri']) as ws:
                    while True:
                        is_end = self.end_record()
                        if is_end:
                            return
                        result = await ws.recv()
                        event_info = self.event_filter(json.loads(result))
                        if event_info:
                            struct_event_info = self.formatter(event_info)
                            self.txt_recorder(struct_event_info)
            except websockets.ConnectionClosedError:
                logger.exception('Ws connection was broken')

    @staticmethod
    def event_filter(event_info: dict) -> bool or dict:
        if event_info['post_type'] != 'message':
            return False
        if event_info['user_id'] != 2944950852:
            print(event_info)
            return False
        return event_info

    def end_record(self) -> bool:
        target = self.end_sub.do_subscribe_nowait()
        if target == self.video_dict['Target']:
            logger.info(f'{self.video_dict["Title"]} Done')
            return True

    def upload_record(self, ddir: str) -> None:
        pub = Publisher()
        upload_dict = {
            'Title': self.video_dict['Title'],
            'Target': self.video_dict['Target'],
            'Path': f'{ddir}/{self.video_dict["Title"]}',
            'User': self.video_dict['User'],
            'Record': True,
            'Origin_Title': self.video_dict['Origin_Title']
        }
        pub.do_publish(upload_dict, 'upload')

    async def main(self) -> None:
        user_config = get_user(self.video_dict['User'])
        if not user_config['record']:
            return None
        ddir = get_ddir(user_config)
        self.video_dict['Origin_Title'] = self.video_dict['Title']
        self.video_dict['Title'] = AdjustFileName(self.video_dict['Title'] + '.txt').adjust(ddir)
        await self.ws_interaction()
        self.upload_record(ddir)


def start() -> None:
    sub = Subscriber(('main',))
    logger.info('Cq worker is already running')
    while True:
        video_dict = sub.do_subscribe()
        if video_dict is not False:
            worker = CQWorker(video_dict)
            asyncio.run(worker.main())


if __name__ == '__main__':
    start()
