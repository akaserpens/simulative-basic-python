import psycopg2
from psycopg2.extras import LoggingConnection
import logging
from contextlib import contextmanager

import simbp.model


def prepare_boolean(value):
    if value is None:
        return None
    if value:
        return 't'
    return 'f'

class DBConnection:
    __instance = None
    __config = None

    @staticmethod
    @contextmanager
    def init(config):
        DBConnection.__config = config
        instance = DBConnection.get_instance()
        try:
            yield instance
        finally:
            instance.close_connect()

    @staticmethod
    def get_instance():
        if not DBConnection.__instance:
            DBConnection()
        return DBConnection.__instance

    def __init__(self):
        if DBConnection.__instance:
            raise Exception("Use DBConnection.get_instance() instead")
        DBConnection.__instance = self
        self.__connection = None

    def close_connect(self):
        if self.__connection:
            self.__connection.close()
            logging.info('Database connection closed')

    def connection(self):
        if not self.__connection:
            if not DBConnection.__config:
                raise Exception("Please call DBConnection.init() to configure connection")
            self.__connection = psycopg2.connect(**DBConnection.__config, connection_factory=LoggingConnection)
            self.__connection.initialize(logging.getLogger('db'))
            logging.info('Database connection established')
        return self.__connection


class AttemptDao:

    @staticmethod
    def insert_many(attempts, chunk_size=1000):
        for i in range(0, len(attempts), chunk_size):
            AttemptDao.__insert_chunk(attempts[i:i + chunk_size])

    @staticmethod
    def __insert_chunk(attempts):
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute("SELECT nextval('attempts_id_seq'::regclass) FROM generate_series(1, %s)", (len(attempts),))
            for x in zip(attempts, cursor):
                x[0].id = x[1][0]

            records_list_template = ','.join(['%s'] * len(attempts))
            values_to_insert = (
                (
                    attempt.id,
                    attempt.user_id,
                    attempt.created_at,
                    attempt.attempt_type,
                    prepare_boolean(attempt.is_correct),
                    attempt.oauth_consumer_key,
                    attempt.lis_result_sourcedid,
                    attempt.lis_outcome_service_url
                )
                for attempt in attempts
            )
            insert_query = f'INSERT INTO attempts (id, user_id, created_at, attempt_type, is_correct, oauth_consumer_key, lis_result_sourcedid, lis_outcome_service_url) VALUES {records_list_template}'
            cursor.execute(insert_query, list(values_to_insert))
            DBConnection.get_instance().connection().commit()

    @staticmethod
    def truncate():
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute('TRUNCATE attempts')
            DBConnection.get_instance().connection().commit()

class TotalsDao:
    @staticmethod
    def count_operations(start, end):
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute('SELECT COUNT(*) '
                           'FROM attempts '
                           'WHERE created_at >= %s '
                           'AND created_at <= %s',
                           (start, end))
            return cursor.fetchone()[0]

    @staticmethod
    def count_total_success(start, end):
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute('SELECT COUNT(*) '
                           'FROM attempts '
                           'WHERE attempt_type = %s '
                           'AND is_correct = true '
                           'AND created_at >= %s '
                           'AND created_at <= %s',
                           (simbp.model.ATTEMPT_TYPE_SUBMIT, start, end))
            return cursor.fetchone()[0]

    @staticmethod
    def count_total_failures(start, end):
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute('SELECT COUNT(*) '
                           'FROM attempts '
                           'WHERE attempt_type = %s '
                           'AND is_correct = false '
                           'AND created_at >= %s '
                           'AND created_at <= %s',
                           (simbp.model.ATTEMPT_TYPE_SUBMIT, start, end))
            return cursor.fetchone()[0]

    @staticmethod
    def count_unique_users(start, end):
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute('SELECT COUNT(DISTINCT user_id) '
                           'FROM attempts '
                           'WHERE created_at >= %s '
                           'AND created_at <= %s',
                           (start, end))
            return cursor.fetchone()[0]

    @staticmethod
    def count_submits_by_users(start, end):
        with DBConnection.get_instance().connection().cursor() as cursor:
            cursor.execute('SELECT user_id, COUNT(*) '
                           'FROM attempts '
                           'WHERE attempt_type = %s '
                           'AND created_at >= %s '
                           'AND created_at <= %s '
                           'GROUP BY user_id',
                           (simbp.model.ATTEMPT_TYPE_SUBMIT, start, end))
            return cursor.fetchall()
