from unittest import TestCase

from bot_worker import filter_at
from download_work import except_set, except_bili, process_video


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


class TestBiliExcept(TestCase):
    def test_except(self):
        except_bili('test', 'Youtube')
        self.assertIn('test', except_set)

        self.assertRaises(RuntimeError, except_bili, 'test', 'BilibiliLive')
        self.assertEqual(except_bili('test', 'Youtube'), None)

        except_set.remove('test')
        self.assertEqual(except_bili('test', 'Bilibili'), None)
