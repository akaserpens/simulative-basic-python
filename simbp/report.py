import logging
import datetime
import gspread
import email.message
import smtplib
from collections import Counter
from simbp.database import TotalsDao as totals
from google.oauth2.service_account import Credentials


class Report:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.unique_users = 0
        self.total_operations = 0
        self.success_submits = 0
        self.failure_submits = 0
        self.avg_submit_per_user = 0

class ReportBuilder:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def build_report(self):
        report = Report(self.start, self.end)
        report.unique_users = self.count_unique_users()
        report.total_operations = self.count_total_operations()
        report.success_submits = self.count_success_submits()
        report.failure_submits = self.count_failure_submits()
        report.avg_submit_per_user = self.count_avg_submits_per_user()
        return report

    def count_unique_users(self):
        return 0

    def count_total_operations(self):
        return 0

    def count_success_submits(self):
        return 0

    def count_failure_submits(self):
        return 0

    def count_avg_submits_per_user(self):
        return 0

class ApiDataReportBuilder(ReportBuilder):
    def __init__(self, start, end, attempts):
        super().__init__(start, end)
        self.attempts = attempts

    def build_report(self):
        logging.info("Building report from api data")
        return super().build_report()

    def count_unique_users(self):
        users = set(a.user_id for a in self.attempts)
        return len(users)

    def count_total_operations(self):
        return len(self.attempts)

    def count_success_submits(self):
        result = [x for x in self.attempts if x.is_success()]
        return len(result)

    def count_failure_submits(self):
        result = [x for x in self.attempts if x.is_failure()]
        return len(result)

    def count_avg_submits_per_user(self):
        by_user = Counter(x.user_id for x in self.attempts if x.is_submit())
        total_submits = sum(x for x in by_user.values())
        result = round (total_submits / len(by_user), 2)
        return result

class DatabaseReportBuilder(ReportBuilder):
    def build_report(self):
        logging.info("Building report from database")
        return super().build_report()

    def count_unique_users(self):
        return totals.count_unique_users(self.start, self.end)

    def count_total_operations(self):
        return totals.count_operations(self.start, self.end)

    def count_success_submits(self):
        return totals.count_total_success(self.start, self.end)

    def count_failure_submits(self):
        return totals.count_total_failures(self.start, self.end)

    def count_avg_submits_per_user(self):
        by_user = totals.count_submits_by_users(self.start, self.end)
        total_submits = sum(x[1] for x in by_user)
        result = round (total_submits / len(by_user), 2)
        return result

class ReportSender:
    def send(self, report):
        pass

class EmailReportSender(ReportSender):
    def __init__(self, mail_config, receiver):
        self.mail_config = mail_config
        self.receiver = receiver

    def send(self, report):
        logging.info(f"Sending report to email {self.receiver}...")
        msg = self._build_email_message(report)
        conn = smtplib.SMTP_SSL(self.mail_config['server'])
        conn.login(self.mail_config['username'], self.mail_config['password'])
        try:
            conn.sendmail(self.mail_config['sender'], self.receiver, msg.as_string())
            logging.info(f"Report email sent")
        except smtplib.SMTPException as e:
            logging.error(f"Failed to send report email: {e}", exc_info=e)
        finally:
            conn.quit()

    def _build_email_message(self, report):
        msg = email.message.EmailMessage()
        msg.set_content(self._report_body(report))
        msg['Subject'] = 'Статистика по задачам'
        msg['From'] = self.mail_config['sender']
        msg['To'] = self.receiver
        return msg

    def _report_body(self, report):
        return f'''
        Статистика за период {report.start.strftime("%d.%m.%Y %H:%M:%S")} - {report.end.strftime("%d.%m.%Y %H:%M:%S")}
        
        Всего операций: {report.total_operations}
        Успешных запусков: {report.success_submits}
        Неуспешных запусков: {report.failure_submits}
        Уникальных пользователей: {report.unique_users}
        В среднем сабмитов на пользователя: {report.avg_submit_per_user}
        
        Отчет сформирован {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
        '''

class GSheetsReportSender(ReportSender):
    def __init__(self, gsheets_config):
        self.gsheets_config = gsheets_config

    def send(self, report):
        logging.info("Uploading report to google sheets...")
        try:
            gc = self._authorize()
            sheet = gc.open_by_key(self.gsheets_config['spreadsheet_key']).worksheet(self.gsheets_config['sheet_name'])
            sheet.append_row(self._report_data(report))
            logging.info("Report uploaded")
        except Exception as e:
            logging.error(f"Failed to upload report to google sheets: {e}", exc_info=e)


    def _authorize(self):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        credentials = Credentials.from_service_account_file(
            self.gsheets_config['credentials'],
            scopes=scopes
        )

        return gspread.authorize(credentials)

    def _report_data(self, report):
        return [
            datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            report.start.strftime("%d.%m.%Y %H:%M:%S"),
            report.end.strftime("%d.%m.%Y %H:%M:%S"),
            report.total_operations,
            report.success_submits,
            report.failure_submits,
            report.unique_users,
            report.avg_submit_per_user,
        ]