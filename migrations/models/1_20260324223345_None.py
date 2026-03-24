from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "articles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(1024) NOT NULL DEFAULT '',
    "link" VARCHAR(2048) NOT NULL DEFAULT '',
    "description" TEXT NOT NULL,
    "abstract" TEXT NOT NULL,
    "publications_type" VARCHAR(100) NOT NULL DEFAULT '',
    "authors" TEXT NOT NULL,
    "published" VARCHAR(100) NOT NULL DEFAULT '',
    "open_access" INT NOT NULL DEFAULT 0,
    "publish_name" VARCHAR(512) NOT NULL DEFAULT '',
    "publish_link" VARCHAR(2048) NOT NULL DEFAULT '',
    "datetime" TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS "artical_match" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "level_match" VARCHAR(20) NOT NULL DEFAULT '',
    "comparison_of_rules" JSON,
    "explanation" TEXT NOT NULL,
    "t_title" VARCHAR(1024) NOT NULL DEFAULT '',
    "t_abstract" TEXT NOT NULL,
    "original_artical_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "result_requests" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "prompt_tokens" INT NOT NULL DEFAULT 0,
    "completion_tokens" INT NOT NULL DEFAULT 0,
    "total_tokens" INT NOT NULL DEFAULT 0,
    "response_model" VARCHAR(100) NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL DEFAULT '',
    "last_name" VARCHAR(255) NOT NULL DEFAULT '',
    "username" VARCHAR(255) NOT NULL UNIQUE,
    "password" VARCHAR(512) NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "email" VARCHAR(255) NOT NULL UNIQUE DEFAULT '',
    "refresh_token" VARCHAR(512),
    "hash_refresh_token" VARCHAR(512),
    "balance" REAL NOT NULL DEFAULT 5,
    "datetime" TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS "authorizations" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "type_auth" VARCHAR(50) NOT NULL DEFAULT '',
    "google_data" JSON,
    "count_uses" INT NOT NULL DEFAULT 0,
    "hash_refresh_token" VARCHAR(128),
    "refresh_expires_at" TIMESTAMP,
    "logout_datetime" TIMESTAMP,
    "datetime" TIMESTAMP NOT NULL,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "avatars" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_object" VARCHAR(1024) NOT NULL,
    "type" VARCHAR(50) NOT NULL DEFAULT '',
    "size" INT NOT NULL DEFAULT 0,
    "thumbnail" VARCHAR(1024),
    "user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "receipts" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "payment_datetime" TIMESTAMP,
    "status" VARCHAR(50) NOT NULL DEFAULT 'pending',
    "price" REAL NOT NULL DEFAULT 0,
    "datetime" TIMESTAMP NOT NULL,
    "user_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "requests" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "field_knowledge" TEXT NOT NULL,
    "target_theme" TEXT NOT NULL,
    "target_context" TEXT NOT NULL,
    "language" VARCHAR(50) NOT NULL DEFAULT '',
    "theme" TEXT NOT NULL,
    "date_from" VARCHAR(20) NOT NULL DEFAULT '',
    "date_to" VARCHAR(20) NOT NULL DEFAULT '',
    "open_access" INT NOT NULL DEFAULT 0,
    "total_amount" INT NOT NULL DEFAULT 0,
    "status" VARCHAR(50) NOT NULL DEFAULT 'process',
    "error_detail" TEXT NOT NULL,
    "datetime" TIMESTAMP NOT NULL,
    "author_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "admin" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "password" VARCHAR(200) NOT NULL,
    "last_login" TIMESTAMP,
    "email" VARCHAR(200) NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "result_request_artical_matches" (
    "result_requests_id" INT NOT NULL REFERENCES "result_requests" ("id") ON DELETE CASCADE,
    "articalmatch_id" INT NOT NULL REFERENCES "artical_match" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_result_requ_result__c5033e" ON "result_request_artical_matches" ("result_requests_id", "articalmatch_id");
CREATE TABLE IF NOT EXISTS "receipt_requests" (
    "receipts_id" INT NOT NULL REFERENCES "receipts" ("id") ON DELETE CASCADE,
    "request_id" INT NOT NULL REFERENCES "requests" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_receipt_req_receipt_ab6244" ON "receipt_requests" ("receipts_id", "request_id");
CREATE TABLE IF NOT EXISTS "request_result_requests" (
    "requests_id" INT NOT NULL REFERENCES "requests" ("id") ON DELETE CASCADE,
    "resultrequest_id" INT NOT NULL REFERENCES "result_requests" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_request_res_request_7c1a5f" ON "request_result_requests" ("requests_id", "resultrequest_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
