# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import (
    redirect,
    render_template
    )
from datetime import datetime, date
from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    get_users_data,
    mean,
    group_by_weekday,
    get_weekday_start_end,
    time_from_seconds
)
import locale
import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


@app.route('/')
def mainpage():
    """
    Presence by weekday page.
    """
    return render_template('presence_weekday.html')


@app.route('/mean_time')
def mean_time_page():
    """
    Presence mean time page
    """
    return render_template('mean_time_weekday.html')


@app.route('/start-end')
def start_end_page():
    """
    Presence start-end page.
    """
    return render_template('presence_start_end.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data, avatar_base_url = get_users_data()
    sort_users = data.keys()
    locale.setlocale(locale.LC_ALL, "")
    sort_users.sort(
        key=lambda user_id: data[user_id]['name'],
        cmp=locale.strcoll
    )
    locale.setlocale(locale.LC_ALL, "C")
    return [
        dict(
            user_id=user_id,
            name=data[user_id]['name'],
            avatar='%s%s' % (
                avatar_base_url,
                data[user_id]['avatar']
            ),
        )
        for user_id in sort_users
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end(user_id):
    """
    Returns mean start and end time by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    mean_hours = get_weekday_start_end(data[user_id])
    today = date.today()
    result = []
    for day, item in mean_hours.iteritems():
        start = datetime.combine(today, time_from_seconds(item['start'])).\
            strftime('%Y-%m-%dT%H:%M:%S')
        end = datetime.combine(today, time_from_seconds(item['end'])).\
            strftime('%Y-%m-%dT%H:%M:%S')
        result.append([day, start, end])

    result.sort(key=lambda a: a[0])
    result = [[calendar.day_abbr[item[0]], item[1], item[2]]
              for item in result]
    return result
