import subprocess
from datetime import datetime
from os.path import isfile, getsize
from threading import Thread
from urllib.parse import quote

import requests

from config import config
from pubsub import Subscriber, Publisher
from tools import check_ddir_is_exist, get_ddir, get_logger, get_user, AdjustFileName

logger = get_logger()


def check_downloaded(paths):
    if isfile(paths):
        logger.info(f'{paths} has been downloaded.')
        return True
    else:
        logger.error(f'{paths} Download error')
        raise RuntimeError


def download_by_streamlink(link: str, title: str, dl_proxy: str, ddir: str,
                           quality: str = 'best') -> str:
    # co = ["streamlink", "--hls-live-restart", "--loglevel", "trace", "--force"]
    co: list = ["streamlink", "--hls-live-restart", "--force"]
    filename: str = title + '.ts'
    paths: str = f'{ddir}/{filename}'
    if config['enable_proxy']:
        co.append('--http-proxy')
        co.append(f'http://{dl_proxy}')
        co.append('--https-proxy')
        co.append(f'https://{dl_proxy}')
    co.append("-o")
    co.append(paths)
    co.append(link)
    co.append(quality)
    subprocess.run(co)
    if check_downloaded(paths):
        return filename


def download_by_youtube_dl(link: str, title: str, dl_proxy: str, ddir: str):
    filename: str = title + '.ts'
    paths: str = f'{ddir}/{filename}'
    co: list = ['youtube-dl', '-o', paths]
    if config['enable_proxy']:
        co.append('--proxy')
        co.append(f'http://{dl_proxy}')
    co.append(link)
    subprocess.run(co)
    if check_downloaded(paths):
        return filename


def get_timestamp():
    return int(datetime.now().timestamp() * 1000)


def download_video(video_dict, ddir):
    if video_dict["Provide"] == 'Youtube':
        result: str = download_by_streamlink(f"https://www.youtube.com/watch?v={video_dict['Ref']}",
                                             video_dict['Title'],
                                             config['proxy'], ddir, config['youtube_quality'])
    elif video_dict["Provide"] == 'Bilibili':
        result: str = download_by_youtube_dl(video_dict['Target'], video_dict['Title'], config['proxy'], ddir)
    else:
        result: str = download_by_streamlink(video_dict['Ref'], video_dict['Title'], config['proxy'], ddir)
    return result


def send_bot(result, user):
    pub = Publisher()
    data = {'Msg': f"[下载提示] {result} 已下载完成，等待上传",
            'User': user}
    logger.warning(data)
    pub.do_publish(data, 'bot')


def send_upload(video_dict, path):
    if not config['enable_upload']:
        return
    pub = Publisher()
    upload_dict = {
        'Title': video_dict['Title'],
        'Target': video_dict['Target'],
        'Date': video_dict['Date'],
        'Path': path,
        'User': video_dict['User'],
        'Origin_Title': video_dict['Origin_Title'],
        'ASS': get_ass(video_dict)
    }
    pub.do_publish(upload_dict, 'upload')
    pub.do_publish(video_dict['Target'], 'cq')


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
    video_dict['Title'] = AdjustFileName(video_dict['Title']).adjust(ddir)
    video_dict['Start_timestamp'] = get_timestamp()
    video_dict['Title'] = download_video(video_dict, ddir)
    video_dict['End_timestamp'] = get_timestamp()
    send_bot(video_dict['Title'], user_config['user'])
    send_upload(video_dict, f'{ddir}/{video_dict["Title"]}')


def get_ass(video_dict: dict) -> str:
    url = f'https://matsuri.huolonglive.com/history?time={video_dict["Start_timestamp"]}|{video_dict["End_timestamp"]}&host=matsuri&ass=1'
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        return ''
    filename: str = f'{video_dict["Title"]}.ass'
    path: str = f'{config["web_dir"]}/ass/{filename}'
    with open(path, 'wb') as f:
        f.write(r.content)
    try:
        if getsize(path) > 885:
            quote_filename: str = quote(f'{filename}')
            return f'ass/{quote_filename}'
        else:
            return ''
    except (FileExistsError, FileNotFoundError):
        return ''


def worker():
    sub = Subscriber(('main', 'download'))
    while True:
        data: dict = sub.do_subscribe()
        if data is not False:
            t = Thread(target=process_video, args=(data,), daemon=True)
            t.start()


if __name__ == '__main__':
    worker()
