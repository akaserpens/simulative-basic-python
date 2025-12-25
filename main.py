#!/usr/bin/env python

import os
import argparse
import configparser
import datetime
import logging
import simbp

def _load_config():
    path_to_config = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(path_to_config)
    return config

def _arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="ISO date/datetime to begin from", type=datetime.datetime.fromisoformat)
    parser.add_argument("--end", help="ISO date/datetime to end with", type=datetime.datetime.fromisoformat)
    parser.add_argument("--truncate", action='store_true', default=False, help="Truncate attempts before fetching new ones")
    parser.add_argument("--no-fetch", action='store_true', default=False, help="Skip fetch attempts")
    args = parser.parse_args()
    return args

def _fetch_attempts(config, args):
    client = simbp.integration.ITResumeClient(**dict(config['itresume']))
    attempts = client.fetch_attempts(args.start, args.end)
    if len(attempts) == 0:
        return
    simbp.database.AttemptDao.insert_many(attempts)


def _run(config, args):
    try:
        logging.info('Start execution')
        if args.truncate:
            logging.info('Truncate attempts')
            simbp.database.AttemptDao.truncate()
        if not args.no_fetch:
            _fetch_attempts(config, args)
        logging.info('Execution successful')
    except Exception as e:
        logging.critical(e, exc_info=e)

def main():
    args = _arguments()
    config = _load_config()
    simbp.logging.init(config['logging'])
    simbp.logging.rotate_logs(config['logging'])
    with simbp.database.DBConnection.init(dict(config['database'])):
        _run(config, args)


if __name__ == "__main__":
    main()