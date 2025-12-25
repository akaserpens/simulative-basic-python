CREATE TABLE "attempts" (
  "id" bigserial NOT NULL,
  PRIMARY KEY ("id"),
  "user_id" text NOT NULL,
  "oauth_consumer_key" text NOT NULL,
  "lis_result_sourcedid" text NOT NULL,
  "lis_outcome_service_url" text NOT NULL,
  "is_correct" boolean NULL,
  "attempt_type" text NOT NULL,
  "created_at" timestamp NOT NULL
);