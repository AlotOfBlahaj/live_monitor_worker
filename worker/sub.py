import json
import redis

pool = redis.ConnectionPool(host='127.0.0.1', port=6379)


class Subscriber:
    def __init__(self):
        self.db = redis.StrictRedis(connection_pool=pool)
        self.sub = self.db.pubsub()
        self.sub.subscribe('main')

    def do_subscribe(self) -> dict:
        data = self.sub.parse_response()
        _data = json.loads(data[2])
        return _data
