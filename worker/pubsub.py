import json
import logging

import redis

pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
logger = logging.getLogger('run.pubsub')


class Subscriber:
    def __init__(self, channel: tuple):
        self.db = redis.StrictRedis(connection_pool=pool)
        self.sub = self.db.pubsub()
        self.sub.subscribe(*channel)
        logger.info('Subscriber is running')

    def do_subscribe(self) -> dict:
        data = self.sub.parse_response()
        logger.info(f'recv {data}')
        if isinstance(data[2], int):
            _data = False
        else:
            _data = json.loads(data[2])
            logger.info(_data)
        return _data


class Publisher:
    def __init__(self):
        self.db = redis.StrictRedis(connection_pool=pool)

    def do_publish(self, data: dict, channel):
        _data = json.dumps(data)
        self.db.publish(channel, _data)
