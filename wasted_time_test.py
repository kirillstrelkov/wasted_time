from time import sleep
from unittest.case import TestCase

from wasted_time import combine_summaries, get_active_window_data


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

        assert combine_summaries(summary1, summary2) == {
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

        assert combine_summaries(summary1, summary2) == {
            'a': {
                '1': 13,
                '2': 10,
                'a total time': 23
            }
        }

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

        assert combine_summaries(summary1, summary2) == {
            'a': {
                '1': 5,
                '2': 7,
                'a total time': 12
            }
        }

    def test_get_active_window_data(self):
        data = get_active_window_data()
        assert data['pid'] > 0
        assert data['app_name'].lower() in ['terminal', 'java']
        assert 'wasted' in data['title'].lower()

    def test_get_active_window_data2(self):
        for _ in range(3):
            data = get_active_window_data()
            assert 'wasted' in data['title']
            assert 'time' in data['title']
            assert data['app_name'] in ['java', 'gnome-terminal-', 'cmd.exe']
            assert data['pid'] > 0
            sleep(0.5)
