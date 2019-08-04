import asyncio

from cq_record import txt_recorder
from cq_ws_core import ws_interaction
from pubsub import Subscriber
from tools import get_logger

logger = get_logger()


async def main(video_dict):
    sub = Subscriber(('upload',))
    while True:
        event = await ws_interaction()
        if event:
            txt_recorder(event, video_dict)
        video_dict = sub.do_subscribe_nowait()
        if video_dict is not False:
            logger.info(f'{video_dict["Title"]} Down')
            break


def worker():
    sub = Subscriber(('main',))
    logger.info('Cq worker is already running')
    while True:
        video_dict = sub.do_subscribe()
        if video_dict is not False:
            asyncio.run(main(video_dict))


if __name__ == '__main__':
    worker()
