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
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

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
