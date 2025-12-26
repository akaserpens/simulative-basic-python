#!/usr/bin/env python

import os
import argparse
import configparser
import datetime
import logging
import simbp

REPORT_SOURCE_DB = 'db'
REPORT_SOURCE_API = 'api'

REPORT_GSHEETS = 'gsheets'
REPORT_EMAIL = 'email'

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
    parser.add_argument("--report-source", help="Calculate totals from database (db) or data from api (api). If not specified, report will not be calculated")
    parser.add_argument("--report", help="email - send totals to email, gsheets - upload totals to Google Sheets")
    parser.add_argument("--email", help="email to send total report to")
    args = parser.parse_args()
    return args

def _fetch_attempts(config, start, end):
    client = simbp.integration.ITResumeClient(**dict(config['itresume']))
    attempts = client.fetch_attempts(start, end)
    if len(attempts) == 0:
        return
    simbp.database.AttemptDao.insert_many(attempts)
    return attempts

def _total_report(config, args, start, end, attempts):
    report_source = args.report_source
    if not report_source:
        logging.info('Report source not specified, report skipped')
        return

    if report_source == REPORT_SOURCE_API:
        if args.no_fetch:
            raise Exception('Fetch disabled, can\'t build report from api data')
        report_builder = simbp.report.ApiDataReportBuilder(start, end, attempts)
    elif report_source == REPORT_SOURCE_DB:
        report_builder = simbp.report.DatabaseReportBuilder(start, end)
    else:
        raise Exception(f'Unknown report source type {report_source}')

    report = report_builder.build_report()

    if args.report == REPORT_GSHEETS:
        sender = simbp.report.GSheetsReportSender(config['gsheets'])
    elif args.report == REPORT_EMAIL:
        if not args.email:
            raise Exception('Email must be specified')
        sender = simbp.report.EmailReportSender(config['mailer'], args.email)
    else:
        raise Exception(f'Unknown report type {args.report}')

    sender.send(report)

def _report_dates(args):
    start = args.start
    end = args.end
    if start is None:
        start = datetime.datetime.now() - datetime.timedelta(hours=24)
    if end is None:
        end = min(start + datetime.timedelta(hours=24), datetime.datetime.now())

    return start, end

def _run(config, args):
    try:
        logging.info('Start execution')
        if args.truncate:
            logging.info('Truncate attempts')
            simbp.database.AttemptDao.truncate()
        start, end = _report_dates(args)
        attempts = None
        if not args.no_fetch:
            attempts = _fetch_attempts(config, start, end)
        _total_report(config, args, start, end, attempts)
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