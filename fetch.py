#!/usr/bin/env python3

"""
A simple status monitor.

Generates a html page from a template and
sends an email to the admin. Additionally it can collect stats about uptimes.
"""

import requests
import re
import datetime
import os
import json

from jinja2 import Template

keep_history = 365  # days
stats_file = 'stats'
hosts = [
    ['https://www.profitopia.de/', 'Profitopia'],
    ['https://help.profitopia.de/', 'Profitopia-Hilfe'],
    ['https://blog.profitopia.de/', 'Profitopia-Blog'],
]
# mail command should contain recipient and have a single {} for subject format
mail_command = '# {}'

overall_oldest_key = None


def check_host(host):
    """Check a single host."""
    try:
        request = requests.get(host[0], timeout=3)
        if re.search(host[1], request.text):
            host[1] = True
        else:
            host[1] = False
    except Exception:
        host[1] = False
    if host[1] is False:
        os.system(mail_command.format('CRITICAL: {} is critical'.format(
            host[0])))

    return host


def get_statistics_for_host(host):
    """Get all collected statistics for specific host."""
    global overall_oldest_key

    stats = {}
    if os.path.isfile(stats_file):
        stats = json.loads(open(stats_file, 'r').read())
    if host not in stats:
        return {}
    stats = stats[host]

    now = datetime.datetime.now()
    now_key = now.strftime('%Y%m%d%H%M')

    sorted_keys = sorted(stats.keys())
    oldest_key = sorted_keys[0]
    if overall_oldest_key is None or oldest_key < overall_oldest_key:
        overall_oldest_key = oldest_key

    result = {}
    for key, min in (
        ('hd', datetime.timedelta(hours=12)),
        ('d', datetime.timedelta(days=1)),
        ('w', datetime.timedelta(weeks=1)),
        ('m', datetime.timedelta(days=30)),
        ('mm', datetime.timedelta(days=90)),
        ('y', datetime.timedelta(days=365)),
    ):
        start_key = (datetime.datetime.now() - min).strftime('%Y%m%d%H%M')
        actual_start_key = start_key

        # find earliest relevant entry
        if start_key in sorted_keys:
            # The start key had a change. It can be used as current state.
            current_state = stats[start_key]
            left_key = start_key
        elif oldest_key < start_key:
            # There are older entries than start_key. Search on the left.
            for c_key in sorted_keys:
                if c_key > start_key:
                    # start_key has already been reached. Stop searching.
                    break
                current_state = stats[c_key]
                left_key = c_key
        else:
            # start_key is older than stats. Can use oldest entry directly.
            current_state = stats[oldest_key]
            actual_start_key = oldest_key
            left_key = actual_start_key

        up_count = 0

        # calculate total count from actual start key and now
        count = calculate_minutes_between_keys(actual_start_key, now)

        keys_including_now = sorted_keys[
            sorted_keys.index(left_key) + 1:]
        if now_key not in sorted_keys:
            keys_including_now += [now_key]

        last_key = actual_start_key

        # loop through relevant list entries from first after left_key
        # til end
        for current_key in keys_including_now:
            if current_state:
                # was up. Add number of minutes to up_count.
                # Subtract 1 in order to exclude current key
                up_count += calculate_minutes_between_keys(
                    last_key, current_key) - 1

            last_key = current_key
            if current_key in stats:
                # conditional as now key is added if not already in.
                current_state = stats[current_key]

        if current_state:
            # was up in last state. Add it now.
            up_count += 1

        result[key] = 100 if count == 0 else 100 * up_count / count
    return result


def calculate_minutes_between_keys(start, end):
    """Caculate the number of minutes gone between two keys/datetimes."""
    if isinstance(start, str):
        start = datetime.datetime.strptime(start, '%Y%m%d%H%M')
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, '%Y%m%d%H%M')

    return ((end - start).total_seconds() // 60)


def renew_status():
    """Fetch the status for all hosts."""
    status = []
    for host, host_pattern in hosts:
        status.append({
            'host': host,
            'status': check_host([host, host_pattern])[1],
        })

    return status


def update_statistics(status):
    """Add an entry to the stats file and delete too old entries."""
    if not os.path.isfile(stats_file):
        current_stats = {}
    else:
        current_stats = json.loads(open(stats_file, 'r').read())
        # current_stats = delete_old_statistics(current_stats)

    current_key = int(datetime.datetime.now().strftime('%Y%m%d%H%M'))
    for host, up in ((h['host'], h['status']) for h in status):
        if host not in current_stats:
            current_stats[host] = {}

        # get newest entry of host
        newest_state = None, None
        for key, entry in current_stats[host].items():
            if newest_state[0] is None or int(key) > int(newest_state[0]):
                newest_state = key, entry
        if newest_state[1] != up:
            # state has changed. Write it.
            current_stats[host][current_key] = up

    # write stats
    open(stats_file, 'w').write(json.dumps(current_stats))


def add_statistics_to_status(status):
    """Add statistics data to status."""
    return [{
        'host': h['host'],
        'status': h['status'],
        'stats': get_statistics_for_host(h['host']),
    } for h in status]


def generate_status_page():
    """Generate a html page containing the status of the pages."""
    status = renew_status()
    now = datetime.datetime.now()

    # update statistics
    update_statistics(status)

    # add stats to status
    status = add_statistics_to_status(status)

    # calculate datetime from oldest key
    stats_first = datetime.datetime.strptime(
        overall_oldest_key, '%Y%m%d%H%M')

    # load template
    template = Template(open('template.html').read())
    print(template.render({
        'time': '{}.{}.{} {:02d}:{:02d}'.format(
            now.day, now.month, now.year, now.hour, now.minute),
        'status': status,
        'stats_first': '{}.{}.{} {:02d}:{:02d}'.format(
            stats_first.day, stats_first.month, stats_first.year,
            stats_first.hour, stats_first.minute),
    }))


if __name__ == '__main__':
    generate_status_page()
