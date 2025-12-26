import requests
import datetime
import logging
import simbp
import ast

ITRESUME_BASE_URL = "https://b2b.itresume.ru/api/statistics"

class ITResumeClient:
    def __init__(self, *, client, client_key, timeout=None):
        self.client = client
        self.client_key = client_key
        self.timeout = None if timeout is None else int(timeout)

    def fetch_attempts(self, start, end):

        logging.info(f"Fetching attempts from {start} to {end}...")
        params = {
            "client": self.client,
            "client_key": self.client_key,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        try:
            response = requests.get(ITRESUME_BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
        except Exception as e:
            logging.info(f"Error fetching attempts: {e}", exc_info=e)
            return []
        data = response.json()
        # data = ast.literal_eval("[{'lti_user_id': 'b09cb4421f0b80eacf771589393eed1e', 'passback_params': \"{'oauth_consumer_key': '', 'lis_result_sourcedid': 'course-v1:SkillFactory+DST-3.0+28FEB2021:lms.skillfactory.ru-fac1cc6ff77544a5bfe71e4c0ba8b2d3:b09cb4421f0b80eacf771589393eed1e'}\", 'is_correct': None, 'attempt_type': 'run', 'created_at': '2025-12-25 10:13:45.439653'}, {'lti_user_id': 'b09cb4421f0b80eacf771589393eed1e', 'passback_params': \"{'oauth_consumer_key': '', 'lis_result_sourcedid': 'course-v1:SkillFactory+DST-3.0+28FEB2021:lms.skillfactory.ru-fac1cc6ff77544a5bfe71e4c0ba8b2d3:b09cb4421f0b80eacf771589393eed1e'}\", 'is_correct': None, 'attempt_type': 'run', 'created_at': '2025-12-25 10:14:25.996518'}, {'lti_user_id': 'b09cb4421f0b80eacf771589393eed1e', 'passback_params': \"{'oauth_consumer_key': '', 'lis_result_sourcedid': 'course-v1:SkillFactory+DST-3.0+28FEB2021:lms.skillfactory.ru-fac1cc6ff77544a5bfe71e4c0ba8b2d3:b09cb4421f0b80eacf771589393eed1e'}\", 'is_correct': None, 'attempt_type': 'run', 'created_at': '2025-12-25 10:14:50.141405'}]")
        if "errors" in data:
            logging.error(f"Error fetching attempts: {data['errors']}")
            return []
        logging.info(f"Fetched {len(data)} attempts")
        return [AttemptTransformer.transform(x) for x in data]

class AttemptTransformer:
    @staticmethod
    def transform(data):
        passback_params = ast.literal_eval(data["passback_params"]) if "passback_params" in data else {}
        basic_params = {
            "id": None,
            "user_id": data.get("lti_user_id"),
            "is_correct": data.get("is_correct"),
            "attempt_type": data.get("attempt_type"),
            "created_at": datetime.datetime.fromisoformat(data.get("created_at")),
        }
        return simbp.model.Attempt(**basic_params, **passback_params)
