import subprocess
from datetime import datetime
from os.path import isfile, getsize
from threading import Thread
from typing import Union

import requests

from config import config
from pubsub import Subscriber, Publisher
from tools import check_ddir_is_exist, get_ddir, get_logger, get_user, AdjustFileName

logger = get_logger()


def downloader(link: str, title: str, dl_proxy: str, ddir: str, user_config: dict,
               quality: str = 'best') -> Union[str, bool]:
    try:
        is_download: bool = user_config['download']
    except KeyError:
        is_download = True
    if is_download:
        # co = ["streamlink", "--hls-live-restart", "--loglevel", "trace", "--force"]
        co: list = ["streamlink", "--hls-live-restart", "--force"]
        if config['enable_proxy']:
            co.append('--http-proxy')
            co.append(f'http://{dl_proxy}')
            co.append('--https-proxy')
            co.append(f'https://{dl_proxy}')
        co.append("-o")
        co.append(f"{ddir}/{title}")
        co.append(link)
        co.append(quality)
        subprocess.run(co)
        paths: str = f'{ddir}/{title}'
        if isfile(paths):
            logger.info(f'{title} has been downloaded.')
            return title
        else:
            logger.error(f'{title} Download error, link: {link}')
            return False
        # 不应该使用os.system


def process_video(video_dict):
    """
    处理直播视频，包含bot的发送，视频下载，视频上传和存入数据库
    :param video_dict: 含有直播视频数据的dict
    :return: None
    """
    user_config: dict = get_user(video_dict['User'])
    if not user_config['download']:
        return None
    ddir: str = get_ddir(user_config)
    check_ddir_is_exist(ddir)
    logger.info(f'{video_dict["Provide"]} Found A Live, starting downloader')
    video_dict['Origin_Title'] = video_dict['Title']
    video_dict['Title'] = AdjustFileName(video_dict['Title'] + '.ts').adjust(ddir)
    video_dict['Start_timestamp'] = int(datetime.now().timestamp() * 1000)
    if video_dict["Provide"] == 'Youtube':
        result: str = downloader(r"https://www.youtube.com/watch?v=" + video_dict['Ref'], video_dict['Title'],
                                 config['proxy'], ddir, user_config, config['youtube_quality'])
    else:
        result: str = downloader(video_dict['Ref'], video_dict['Title'], config['proxy'], ddir, user_config)
    pub = Publisher()
    if result:
        video_dict['End_timestamp'] = int(datetime.now().timestamp() * 1000)
        data = {'Msg': f"[下载提示] {result} 已下载完成，等待上传",
                'User': user_config['user']}
        logger.warning(data)
        pub.do_publish(data, 'bot')
    if config['enable_upload']:
        upload_dict = {
            'Title': video_dict['Title'],
            'Target': video_dict['Target'],
            'Date': video_dict['Date'],
            'Path': f'{ddir}/{video_dict["Title"]}',
            'User': video_dict['User'],
            'Origin_Title': video_dict['Origin_Title'],
            'ASS': get_ass(video_dict)
        }
        pub.do_publish(upload_dict, 'upload')
        pub.do_publish(video_dict['Target'], 'cq')


def get_ass(video_dict: dict) -> str:
    url = f'https://matsuri.huolonglive.com/history?time={video_dict["Start_timestamp"]}|{video_dict["End_timestamp"]}&host=matsuri&ass=1'
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        return ''
    path = f'{config["web_dir"]}/ass/{video_dict["Title"]}.ass'
    with open(path, 'wb') as f:
        f.write(r.content)
    try:
        if getsize(path) > 885:
            return f'ass/{video_dict["Title"]}.ass'
        else:
            return ''
    except FileExistsError:
        return ''


def worker():
    sub = Subscriber(('main',))
    while True:
        data: dict = sub.do_subscribe()
        if data is not False:
            t = Thread(target=process_video, args=(data,), daemon=True)
            t.start()


if __name__ == '__main__':
    worker()
