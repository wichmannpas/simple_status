#!/usr/bin/env python3
import requests
import re
import datetime
from jinja2 import Template

hosts = [
    ['http://www.profitopia.de/', 'Profitopia'],
    ['http://help.profitopia.de/', 'Profitopia-Hilfe'],
    ['http://blog.profitopia.de/', 'Profitopia-Blog'],
]


def check_host(host):
    """Check a single host."""
    try:
        request = requests.get(host[0])
        if re.search(host[1], request.text):
            host[1] = True
        else:
            host[1] = False
    except Exception:
        host[1] = False
    return host


def renew_status():
    """Fetch the status for all hosts."""
    status = []
    for host in hosts:
        status.append(check_host(host))

    return status


def generate_status_page():
    """Generate a html page containing the status of the pages."""
    status = renew_status()
    now = datetime.datetime.now()

    # load template
    template = Template(open('template.html').read())
    print(template.render({
        'time': '{}.{}.{} {}:{}'.format(now.day, now.month, now.year, now.hour, now.minute),
        'status': status,
    }))


if __name__ == '__main__':
    generate_status_page()
