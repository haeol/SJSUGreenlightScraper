# San Jose State Club Organization database population scraper 
# Written by Kevin Tom

import sys
import os
import subprocess
import json
import argparse
try:
    from ConfigParser import ConfigParser
except:
    from configparser import ConfigParser

from session import (GreenlightScraper, GreenlightSession)

# json metadata format for seed.rb
'''
orgs = {
    'name' : {
        'classification' : 'string',
        'officers' : [],
        'description' : 'string'
    }
}
'''

_JSON_METADATA = 'metadata.json'

def parse_cmd():

    parser = argparse.ArgumentParser(description='Admin Web Scraper')
    # Website does not require any sensitive information for now
    parser.add_argument('-u', '-id', '--user', '--sid',
                        required=False,
                        help='Specify the SJSU user ID'
    )
    parser.add_argument('-p', '-pw', '--password',
                        required=False,
                        help='Specify the SJSU user\'s password'
    )
    return parser.parse_args()


def verify(cmds):

    if cmds.user:
        if not cmds.password:
            raise Exception('Password required with user')
    elif cmds.password:
        raise Exception('User required with password')


def run_seed():

    subprocess.call(['rake', 'RAILS_ENV=test', 'db:seed'])


def json_check(data):

    metadata_path = sys.path[0] + '/' + _JSON_METADATA
    if not os.path.isfile(metadata_path):
        print('Metadata path does not exist')
        past = {}
    else:
        # test if metadata is different
        with open(metadata_path, 'r') as f:
            past = json.load(f)

    # convert to consistent json format
    present = json.dumps(data)
    past = json.dumps(past)
    if past == present:
        return True

    # not the same, find differences and write to separate json files
    update_json(json.loads(past), json.loads(present))
    return False


def update_json(old, new):

    _create = {}
    _update = {}
    _delete = {}

    oldkeys = set(old.keys())
    newkeys = set(new.keys())

    deletekeys = oldkeys - newkeys
    createkeys = newkeys - oldkeys
    updatekeys = newkeys & oldkeys

    print("delete keys: %i" % len(deletekeys))
    print("create keys: %i" % len(createkeys))

    count = 0
    for k in deletekeys:
        _delete[k] = old[k]
    for k in createkeys:
        _create[k] = new[k]
    for k in updatekeys:
        if old[k] != new[k] and set(old[k]["officers"]) != set(new[k]["officers"]):
            count += 1
            _update[k] = new[k]

    print("update keys: %i" % count)


    with open(sys.path[0] + '/CRUD/delete.json', 'w') as f:
        json.dump(_delete, f, indent=4)
    with open(sys.path[0] + '/CRUD/update.json', 'w') as f:
        json.dump(_update, f, indent=4)
    with open(sys.path[0] + '/CRUD/create.json', 'w') as f:
        json.dump(_create, f, indent=4)


def main(cmds):

    if not (cmds.user and cmds.password):
        config = ConfigParser()
        config_loc = sys.path[0] + '/config.ini'
        config.read(config_loc)
        username = config.get('user-info', 'username')
        password = config.get('user-info', 'password')

    else:
        username = cmds.user
        password = cmds.password

    sess = GreenlightSession(username, password)
    scraper = GreenlightScraper(sess)
    if not scraper.scrape():
        raise Exception('Scrape failed to retrieve valid requests')

    # Write metadata to file
    if not json_check(scraper.orgs):
        print('Metadata not the same, rewriting')
        with open(sys.path[0] + '/' + _JSON_METADATA, 'w') as f:
            json.dump(scraper.orgs, f, indent = 4)
        print('Seeding into database')
        subprocess.call(['rake', 'RAILS_ENV=test', 'db:seed'])
    else:
        print('Metadata the same, no update needed')

    print('Process complete')


if __name__ == '__main__':
    cmds = parse_cmd()
    verify(cmds)
    main(cmds)

