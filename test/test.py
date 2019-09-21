from unittest import TestCase

from bot_worker import filter_at
from download_work import process_video
from tools import AdjustFileName


class TestFilter_at(TestCase):
    def test_filter_at(self):
        self.assertEqual(filter_at('w', '1[CQ:at,qq=all]'), '1[CQ:at,qq=all]')
        self.assertEqual(filter_at('w', '2[CQ:at,qq=all]'), '2')
        self.assertEqual(filter_at('e', '3[CQ:at,qq=all]'), '3[CQ:at,qq=all]')


class Testdownload_work(TestCase):
    def test_download_work(self):
        video_dict = {
            'User': 'natsuiromatsuri',
            'Provide': 'Youtube',
            'Title': 'test',
            'Ref': '0ThrDxUh9_Q',
            'Target': 'https://www.youtube.com/watch?v=0ThrDxUh9_Q'
        }
        process_video(video_dict)


class TestAdjustFileName(TestCase):
    def test_remove_emoji(self):
        a = AdjustFileName('''startspreadingthenews yankees win great start by 🎅🏾 going 5strong innings with 5k’s🔥 🐂
... solo homerun 🌋🌋 with 2 solo homeruns and👹 3run homerun… 🤡 🚣🏼 👨🏽‍⚖️ with rbi’s … 🔥🔥
... 🇲🇽 and 🇳🇮 to close the game🔥🔥!!!….''')
        a.remove_emoji()
        print(a.filename)
        self.assertEqual(a.filename, '''startspreadingthenews yankees win great start by # going 5strong innings with 5k’s# #
... solo homerun ## with 2 solo homeruns and# 3run homerun… # # # with rbi’s … ##
... # and # to close the game##!!!….''')