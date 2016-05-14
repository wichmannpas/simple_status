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

check_interval = 5  # minutes
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


def renew_status():
    """Fetch the status for all hosts."""
    status = []
    for host in hosts:
        status.append(check_host(host))

    return status


def update_statistics(status):
    """Add an entry to the stats file and delete too old entries."""
    if not os.path.isfile(stats_file):
        current_stats = {}
    else:
        current_stats = json.loads(open(stats_file, 'r').read())
        current_stats = delete_old_statistics(current_stats)

    current_key = datetime.datetime.now().strftime('%Y%m%d%H%M')
    for host, up in status:
        if host not in current_stats:
            current_stats[host] = {}

        # add current measurement
        current_stats[host][current_key] = up

    # write stats
    open(stats_file, 'w').write(json.dumps(current_stats))


def delete_old_statistics(stats):
    """Delete too old statistics."""
    # TODO
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
