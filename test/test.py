from unittest import TestCase

from bot_worker import filter_at, call_bot
from download_work import current_live, check_duplicate, process_video, get_trans_ass, send_hls, end_live
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

    def test_get_trans_ass(self):
        title = 'test'
        s_t = 157110150220
        e_t = 1565700952162
        ass, txt = get_trans_ass(title, s_t, e_t)
        self.assertEqual('ass/test.ass', ass)
        self.assertEqual('txt/test.txt', txt)
        s_t = 0
        e_t = 0
        ass, txt = get_trans_ass(title, s_t, e_t)
        self.assertEqual('', ass)
        self.assertEqual('', txt)


class TestBiliExcept(TestCase):
    def test_except(self):
        check_duplicate('test')
        self.assertIn('test', current_live)

        self.assertRaises(RuntimeError, check_duplicate, 'test')
        end_live('test')
        self.assertEqual(check_duplicate('test'), None)


class TestCallHls(TestCase):
    def test_call(self):
        send_hls('pikurusu_003575630177', 'C:/Users/FZxia/Downloads',
                 'C:/Users/FZxia/Downloads/pikurusu_003575630177.flv')


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


class TestBot(TestCase):
    def test_call_bot(self):
        video_dict = {
            'Msg': '[CQ:at,qq=all]',
            'User': 'pikurusu'
        }
        call_bot(video_dict)
        self.skipTest('success')
