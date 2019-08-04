import subprocess
from os.path import isfile
from threading import Thread

from config import config
from pubsub import Subscriber, Publisher
from tools import check_ddir_is_exist, get_ddir, get_logger, get_user, AdjustFileName

logger = get_logger()


def downloader(link, title, dl_proxy, ddir, user_config, quality='best'):
    try:
        is_download = user_config['download']
    except KeyError:
        is_download = True
    if is_download:
        # co = ["streamlink", "--hls-live-restart", "--loglevel", "trace", "--force"]
        co = ["streamlink", "--hls-live-restart", "--force"]
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
        paths = f'{ddir}/{title}'
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
    user_config = get_user(video_dict['User'])
    assert 'bot_notice' in user_config
    assert 'download' in user_config
    ddir = get_ddir(user_config)
    check_ddir_is_exist(ddir)
    logger.info(f'{video_dict["Provide"]} Found A Live, starting downloader')
    video_dict['Title'] = AdjustFileName(video_dict['Title']).adjust(ddir)
    if video_dict["Provide"] == 'Youtube':
        result = downloader(r"https://www.youtube.com/watch?v=" + video_dict['Ref'], video_dict['Title'],
                            config['proxy'], ddir, user_config, config['youtube_quality'])
    else:
        result = downloader(video_dict['Ref'], video_dict['Title'], config['proxy'], ddir, user_config)
    pub = Publisher()
    if result:
        data = {'Msg': f"[下载提示] {result} 已下载完成，等待上传",
                'User': user_config['User']}
        pub.do_publish(data, 'bot')
    if config['enable_upload']:
        pub.do_publish(video_dict, 'upload')
        pub.do_publish(video_dict, 'cq')


def worker():
    sub = Subscriber(('main',))
    while True:
        data = sub.do_subscribe()
        if data is not False:
            t = Thread(target=process_video, args=(data,), daemon=True)
            t.start()


if __name__ == '__main__':
    worker()
