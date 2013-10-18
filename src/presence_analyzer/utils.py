# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
from lxml import etree
from json import dumps
from functools import wraps
from datetime import datetime, time

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)
            else:
                data.setdefault(user_id, {})[date] = {'start': start,
                                                      'end': end}

    return data


def get_users_data():
    """
    Extracts users data from xml file

    It creates structure like this:
    {
        'user_id':{
            'avatar': avatar_url,
            'name': name
        }
    }
    """
    user_data = {}
    avatar_base_url = None
    try:
        tree = etree.parse(app.config['DATA_PATH'])
    except IOError:
        log.debug('Problem with parse xml file', exc_info=True)
    else:
        root = tree.getroot()
        host = root.find('server').find('host').text
        protocol = root.find('server').find('protocol').text
        avatar_base_url = '%s://%s' % (protocol, host)
        users_element = root.find('users')
        for user in users_element.getchildren():
            user_data[user.get('id')] = {
                element.tag: element.text for element in user.getchildren()
            }
    return user_data, avatar_base_url


def get_weekday_start_end(items):
    """
    Get start time and end time by weekdays
    """
    result = {}
    for date in items:
        week_day = date.weekday()
        if not week_day in result.keys():
            result[week_day] = {'start': [], 'end': []}
        result[week_day]['start'].append(
            seconds_since_midnight(items[date]['start'])
        )
        result[week_day]['end'].append(
            seconds_since_midnight(items[date]['end'])
        )

    result = {key: {'start': int(mean(item['start'])),
                    'end': int(mean(item['end']))}
              for (key, item) in result.iteritems()}
    return result


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def time_from_seconds(seconds):
    """
    Convert seconds since midgnight to time
    """
    hour, seconds = divmod(seconds, 3600)
    minute, second = divmod(seconds, 60)
    try:
        return time(hour, minute, second)
    except ValueError:
        return None


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
