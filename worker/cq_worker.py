import asyncio

from cq_record import txt_recorder
from cq_ws_core import ws_interaction
from pubsub import Subscriber, Publisher
from tools import get_logger, AdjustFileName, get_user, get_ddir

logger = get_logger()


async def main(video_dict):
    sub = Subscriber(('cq',))
    user_config = get_user(video_dict['User'])
    ddir = get_ddir(user_config)
    video_dict['Title'] = AdjustFileName(video_dict['Title']).adjust(ddir)
    while True:
        event = await ws_interaction()
        if event:
            txt_recorder(event, video_dict)
        video_dict = sub.do_subscribe_nowait()
        if video_dict is not False:
            logger.info(f'{video_dict["Title"]} Done')
            pub = Publisher()
            upload_dict = {
                'Title': video_dict['Title'] + '.txt',
                'User': video_dict['User'],
                'Record': True
            }
            pub.do_publish(upload_dict, 'upload')
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
