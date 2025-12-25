ATTEMPT_TYPE_RUN = "run"
ATTEMPT_TYPE_SUBMIT = "submit"

class Attempt:
    def __init__(self, *, id, user_id, created_at, attempt_type, is_correct=None, oauth_consumer_key='', lis_result_sourcedid='', lis_outcome_service_url=''):
        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.attempt_type = attempt_type
        self.is_correct = is_correct
        self.oauth_consumer_key = oauth_consumer_key
        self.lis_result_sourcedid = lis_result_sourcedid
        self.lis_outcome_service_url = lis_outcome_service_url

    def is_run(self):
        return self.attempt_type == ATTEMPT_TYPE_RUN

    def is_submit(self):
        return self.attempt_type == ATTEMPT_TYPE_SUBMIT
