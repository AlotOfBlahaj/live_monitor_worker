import asyncio
import json
from datetime import datetime

import websockets


async def ws_interaction():
    while True:
        try:
            uri = ''
            async with websockets.connect(uri) as ws:
                while True:
                    result = await ws.recv()
                    event_info = event_filter(json.loads(result))
                    if event_info:
                        struct_event_info = formatter(event_info)
                        return struct_event_info
                    else:
                        return False
        except Exception:
            pass


def event_filter(event_info):
    if event_info['post_type'] != 'message':
        return False
    if event_info['user_id'] != 2944950852:
        print(event_info)
        return False
    return event_info


def formatter(event_info):
    def time_formatter():
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


if __name__ == '__main__':
    asyncio.run(ws_interaction())
