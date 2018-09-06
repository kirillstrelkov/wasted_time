from time import sleep
from unittest.case import TestCase

from nose.tools import assert_equal

from wasted_time import combine_summaries, get_active_window_name


class WastedTimeTest(TestCase):
    def test_combine_different_summaries(self):
        summary1 = {
            'a': {
                '1': 5,
                '2': 3
            }
        }

        summary2 = {
            'b': {
                'i': 5,
                'ii': 7,
            }
        }

        assert_equal(
            combine_summaries(summary1, summary2), {
                'a': {
                    '1': 5,
                    '2': 3,
                    'a total time': 8
                },
                'b': {
                    'i': 5,
                    'ii': 7,
                    'b total time': 12
                }
            }
        )

    def test_combine_simple_summaries(self):
        summary1 = {
            'a': {
                '1': 5,
                '2': 3
            }
        }

        summary2 = {
            'a': {
                '1': 8,
                '2': 7,
            }
        }

        assert_equal(
            combine_summaries(summary1, summary2), {
                'a': {
                    '1': 13,
                    '2': 10,
                    'a total time': 23
                }
            }
        )

    def test_combine_simple_summaries2(self):
        summary1 = {
            'a': {
                '1': 5,
            }
        }

        summary2 = {
            'a': {
                '2': 7,
            }
        }

        assert_equal(
            combine_summaries(summary1, summary2), {
                'a': {
                    '1': 5,
                    '2': 7,
                    'a total time': 12
                }
            }
        )


class WastedTimeTest(TestCase):
    def test_get_active_window_name(self):
        while True:
            print(get_active_window_name())
            sleep(5)
            # assert_equal(get_active_window_name(), 'sdf')
