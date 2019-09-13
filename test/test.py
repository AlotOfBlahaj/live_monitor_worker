from unittest import TestCase

from bot_worker import filter_at


class TestFilter_at(TestCase):
    def test_filter_at(self):
        self.assertEqual(filter_at('w', '1[CQ:at,qq=all]'), '1[CQ:at,qq=all]')
        self.assertEqual(filter_at('w', '2[CQ:at,qq=all]'), '2')
        self.assertEqual(filter_at('e', '3[CQ:at,qq=all]'), '3[CQ:at,qq=all]')
