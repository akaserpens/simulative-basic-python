import os
import logging
import datetime
import glob
import re

def init(config):
    level_dict = {
        "critical": logging.CRITICAL,
        "fatal": logging.FATAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "warn": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }
    level_config = config.get("level").lower()
    level = level_dict[level_config] if level_config in level_dict else logging.INFO

    log_path = _get_log_dir(config)
    log_file = None
    if log_path:
        log_file = str(os.path.join(
            log_path,
            "{}.log".format(datetime.date.today().strftime("app-%Y-%m-%d"))
        ))

    logging.basicConfig(
        filename=log_file,
        format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
        level=level
    )

def rotate_logs(config):
    keep_days = config.getint("keep_days")
    log_path = _get_log_dir(config)
    today = datetime.date.today()
    if not log_path or not keep_days:
        return
    files = glob.glob(log_path + "/app-*.log")
    for file in files:
        m = re.search(r"app-(\d{4}-\d{2}-\d{2}).log", os.path.basename(file))
        if not m:
            continue
        try:
            log_date = datetime.datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        if today - log_date > datetime.timedelta(days=keep_days - 1):
            os.remove(file)

def _get_log_dir(config):
    log_dir = config.get("path")
    if not log_dir:
        return None
    return str(os.path.join(
        os.path.dirname(__file__),
        "../",
        log_dir
    ))



