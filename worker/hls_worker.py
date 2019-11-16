import subprocess
from os import mkdir, listdir
from threading import Thread

from pubsub import Subscriber, Publisher


class HlsGeneration:
    def __init__(self, data):
        self.title = data['Title']
        self.source_path = data['Path']
        self.ddir = data['Ddir']
        self.m3u8_path = f'{self.ddir}/{self.title}'

    def generation_hls_by_ffmpeg(self):
        mkdir(f'{self.ddir}/{self.title}')
        slice_command = ['ffmpeg', '-i', self.source_path, '-c', 'copy', '-map', '0', '-f', 'segment', '-segment_list',
                         f'{self.m3u8_path}/{self.title}.m3u8', '-segment_time', '10',
                         f'{self.m3u8_path}/{self.title}%03d.ts']
        subprocess.run(slice_command)

    def call_upload(self):
        upload_handler = UploadHls(self.m3u8_path)
        upload_handler.generation_uploader()

    def call_hls_generation(self):
        # self.generation_hls_by_ffmpeg()
        self.call_upload()


class UploadHls:
    def __init__(self, m3u8_path):
        self.m3u8_path = m3u8_path

    def generation_uploader(self):
        hls_list = listdir(self.m3u8_path)
        for seg in hls_list:
            self.uploader(seg, f'{self.m3u8_path}/{seg}')

    @staticmethod
    def uploader(filename, path):
        upload_dict = {
            'Path': path,
            'Filename': filename,
            'Is_m3u8': True
        }
        pub = Publisher()
        pub.do_publish(upload_dict, 'upload')


def sub_thread():
    sub = Subscriber(('hls',))
    while True:
        data: dict = sub.do_subscribe()
        if data is not False:
            worker = HlsGeneration(data)
            t = Thread(target=worker.call_hls_generation, daemon=True)
            t.start()


if __name__ == '__main__':
    sub_thread()
