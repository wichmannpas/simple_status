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

from copy import deepcopy
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
    stats = json.loads(open(stats_file, 'r').read())
    if host not in stats:
        return {}
    stats = stats[host]

    result = {}
    for key, min in (
        ('hd', datetime.timedelta(hours=12)),
        ('d', datetime.timedelta(days=1)),
        ('w', datetime.timedelta(weeks=1)),
        ('m', datetime.timedelta(days=30)),
        ('mm', datetime.timedelta(days=90)),
        ('y', datetime.timedelta(days=365)),
    ):
        count = 0
        up_count = 0
        # filter stats of host for all relevant entries
        for time, up in stats.items():
            if datetime.datetime.strptime(
                    time, '%Y%m%d%H%M') < datetime.datetime.now() - min:
                continue
            count += 1
            if up:
                up_count += 1
        result[key] = 100 if count == 0 else 100 * up_count / count
    return result


def renew_status():
    """Fetch the status for all hosts."""
    status = []
    for host, host_status in hosts:
        status.append({
            'host': host,
            'status': host_status,
            'stats': get_statistics_for_host(host),
        })

    return status


def update_statistics(status):
    """Add an entry to the stats file and delete too old entries."""
    if not os.path.isfile(stats_file):
        current_stats = {}
    else:
        current_stats = json.loads(open(stats_file, 'r').read())
        current_stats = delete_old_statistics(current_stats)

    current_key = datetime.datetime.now().strftime('%Y%m%d%H%M')
    for host, up in ((h['host'], h['status']) for h in status):
        if host not in current_stats:
            current_stats[host] = {}

        # add current measurement
        current_stats[host][current_key] = up

    # write stats
    open(stats_file, 'w').write(json.dumps(current_stats))


def delete_old_statistics(stats):
    """Delete too old statistics."""
    min = datetime.datetime.now() - datetime.timedelta(days=keep_history)
    for host, entries in deepcopy(stats).items():
        for entry in entries.keys():
            if datetime.datetime.strptime(entry, '%Y%m%d%H%M') < min:
                del stats[host][entry]
    return stats


def generate_status_page():
    """Generate a html page containing the status of the pages."""
    status = renew_status()
    now = datetime.datetime.now()

    # update statistics
    update_statistics(status)

    # load template
    template = Template(open('template.html').read())
    print(template.render({
        'time': '{}.{}.{} {:02d}:{:02d}'.format(
            now.day, now.month, now.year, now.hour, now.minute),
        'status': status,
    }))


if __name__ == '__main__':
    generate_status_page()
