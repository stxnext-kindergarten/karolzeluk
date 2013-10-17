# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest
import random
import calendar
from mock import patch
from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()
        self.test_data = utils.get_data()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test presence by weekday page
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_start_end_page(self):
        """
        Test start-end page
        """
        resp = self.client.get('/start-end')
        self.assertEqual(resp.status_code, 200)

    def test_mean_time_page(self):
        """
        Test mean time page
        """
        resp = self.client.get('/mean_time')
        self.assertEqual(resp.status_code, 200)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_mean_time_weekday(self):
        """
        Test mean presence time of random user grouped by weekday.
        """
        user_id = random.choice(self.test_data.keys())
        resp = self.client.get('/api/v1/mean_time_weekday/%s' % (user_id, ))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = resp.data
        weekdays = utils.group_by_weekday(self.test_data[user_id])
        result = json.dumps(
            [(calendar.day_abbr[weekday], utils.mean(intervals))
                for weekday, intervals in weekdays.items()])
        self.assertEqual(data, result)

        fake_user_id = 1
        resp = self.client.get('/api/v1/mean_time_weekday/%s' %
                               (fake_user_id, ))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = []
        self.assertEqual(data, result)

    def test_presence_weekday_view(self):
        """
        Test total presence time of given user grouped by weekday.
        """
        user_id = random.choice(self.test_data.keys())
        resp = self.client.get('/api/v1/presence_weekday/%s' % (user_id, ))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = resp.data
        weekdays = utils.group_by_weekday(self.test_data[user_id])
        result = [(calendar.day_abbr[weekday], sum(intervals))
                  for weekday, intervals in weekdays.items()]
        result.insert(0, ('Weekday', 'Presence (s)'))
        result = json.dumps(result)
        self.assertEqual(data, result)

        fake_user_id = 1
        resp = self.client.get('/api/v1/presence_weekday/%s' %
                               (fake_user_id, ))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        result = []
        self.assertEqual(data, result)

    def test_presence_start_end(self):
        """
        Test mean start and end time by weekday
        """
        user_id = 10
        resp = self.client.get('/api/v1/presence_start_end/%s' % (user_id, ))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        d = datetime.date.today()
        result = [[unicode(calendar.day_abbr[item_date.weekday()]),
                   unicode(datetime.datetime.combine(
                       d,
                       item['start']).strftime('%Y-%m-%dT%H:%M:%S')),
                   unicode(datetime.datetime.combine(
                       d,
                       item['end']).strftime('%Y-%m-%dT%H:%M:%S'))]
                  for (item_date, item) in self.test_data[user_id].iteritems()]
        self.assertItemsEqual(data, result)

        fake_user_id = 1
        resp = self.client.get('/api/v1/presence_start_end/%s' %
                               (fake_user_id, ))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(data, [])


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

        with patch('csv.reader') as mock_reader:
            mock_reader.return_value = [[],
                                        [1, 2, 3, 4, 5],
                                        ['3a', '2012-12-31', '0:0:0', '0:0:1'],
                                        ['3', '2012-12-51', '0:0:0', '0:0:1']]
            data = utils.get_data()
            self.assertItemsEqual(data, {})

    def test_group_by_weekday(self):
        """
        Test grouping presence entries by weekday.
        """
        data = utils.get_data()
        result = utils.group_by_weekday(data[10])
        self.assertIsInstance(result, dict)
        self.assertItemsEqual(result.keys(), range(7))
        self.assertItemsEqual(result[2], [24465])
        self.assertItemsEqual(result[6], [])

    def test_seconds_since_midnight(self):
        sample_date = datetime.datetime(2013, 9, 10)

        date = datetime.datetime(2013, 9, 10, 0, 0, 0)
        delta = date - sample_date
        result = utils.seconds_since_midnight(date)
        self.assertEqual(int(delta.total_seconds()), result)

        date = datetime.datetime(2013, 9, 10, 23, 59, 59)
        delta = date - sample_date
        result = utils.seconds_since_midnight(date)
        self.assertEqual(int(delta.total_seconds()), result)

    def test_interval(self):
        start_date = datetime.datetime(2013, 9, 10, 1, 2, 3)

        end_date = datetime.datetime(2013, 9, 10, 20, 50, 20)
        delta = end_date - start_date
        result = utils.interval(start_date, end_date)
        self.assertEqual(int(delta.total_seconds()), result)

        end_date = datetime.datetime(2013, 9, 10, 23, 59, 59)
        delta = end_date - start_date
        result = utils.interval(start_date, end_date)
        self.assertEqual(int(delta.total_seconds()), result)

    def test_mean(self):
        """
        Test calculating mean of list
        """
        self.assertEqual(utils.mean([]), 0)
        items = [34]
        self.assertEqual(utils.mean(items), 34)

    def test_time_from_seconds(self):
        """
        Test converting seconds from midnight to time
        """
        time = datetime.time(0, 0, 0)
        self.assertEqual(time, utils.time_from_seconds(0))

        time = datetime.time(23, 59, 59)
        result = utils.time_from_seconds(utils.seconds_since_midnight(time))
        self.assertEqual(time, result)

        seconds = 4333333335
        self.assertEqual(utils.time_from_seconds(seconds), None)

    def test_get_weekday_start_end(self):
        """
        Test getting start and end time grouping by weekdays
        """
        data = utils.get_data()
        result = utils.get_weekday_start_end(data[10])
        correct_result = {1: {'start': 34745, 'end': 64792},
                          2: {'start': 33592, 'end': 58057},
                          3: {'start': 38926, 'end': 62631}}
        self.assertEqual(result, correct_result)
        self.assertEqual(utils.get_weekday_start_end({}), {})


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
