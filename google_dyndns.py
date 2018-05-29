#!/usr/bin/env python

import os
from pathlib import Path
from ipaddress import ip_address
import logging
from logging.handlers import SysLogHandler

import requests
from bs4 import BeautifulSoup


def update_dns_entry(new_ip):
    url = f'https://domains.google.com/nic/update?hostname={os.environ["DYNDNS_HOSTNAME"]}&myip={new_ip}'
    auth = (os.environ['DYNDNS_USERNAME'], os.environ['DYNDNS_PASSWORD'])
    r = requests.post(url=url, auth=auth)
    logger.info(f'Google Domains response: {r.text}')
    if not r.text.startswith('good'):
        logger.info('IP address successfully changed')
        return True
    elif r.text.startswith('nochg'):
        logger.error('No change in IP address...why was this function called?')
        return False
    else:
        logger.error('Error updating domain!')
        return False


def get_new_ip():
    new_ip = None

    r = requests.get('https://api.ipify.org?format=json')
    new_ip = r.json()['ip']

    if not new_ip:
        r = requests.get('http://checkip.dyndns.org')
        parsed = BeautifulSoup(r.text, 'html.parser')
        new_ip = parsed.body.text.split(': ')[1]

    try:
        ip_address(new_ip)
    except ValueError:
        logger.error('Incorrect IP Address parsed from response')
        raise

    return new_ip.strip()


def get_old_ip():
    script_dir = Path(__file__).parents[0]
    old_ip_path = script_dir / 'old_ip.txt'

    old_ip = None
    with open(old_ip_path) as f:
        old_ip = f.read()

    if not old_ip:
        raise Exception('error reading old ip')

    return old_ip.strip()


def log_ip(new_ip):
    script_dir = Path(__file__).parents[0]
    old_ip_path = script_dir / 'old_ip.txt'
    with open(old_ip_path, 'w') as f:
        f.write(new_ip)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__file__)
    handler = SysLogHandler(address='/dev/log')
    logger.addHandler(handler)

    old_ip = get_old_ip()
    logger.debug(f'old_ip = {old_ip}')
    new_ip = get_new_ip()
    logger.debug(f'new_ip = {new_ip}')

    if old_ip == new_ip:
        logger.info(f'IP address {old_ip} has not changed since last check')
    else:
        logger.info(f'IP address {old_ip} has changed to {new_ip} since last check')
        if update_dns_entry(new_ip):
            log_ip(new_ip)
