-- Auto-generated from SQLite astrology.db

DROP TABLE IF EXISTS "users" CASCADE;
CREATE TABLE "users" (
    "userid" INTEGER,
    "phone" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "role" TEXT DEFAULT 'user',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT DEFAULT '',
    "email" TEXT,
    PRIMARY KEY ("userid")
);

DROP TABLE IF EXISTS "planet_nakshatra_interpretations" CASCADE;
CREATE TABLE "planet_nakshatra_interpretations" (
    "id" SERIAL,
    "planet" TEXT NOT NULL,
    "nakshatra" TEXT NOT NULL,
    "house" INTEGER NOT NULL,
    "interpretation" TEXT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "password_reset_codes" CASCADE;
CREATE TABLE "password_reset_codes" (
    "id" SERIAL,
    "phone" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires_at" TIMESTAMP NOT NULL,
    "used" TEXT DEFAULT 'FALSE',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "daily_prediction_rules" CASCADE;
CREATE TABLE "daily_prediction_rules" (
    "id" TEXT,
    "rule_type" TEXT NOT NULL,
    "conditions" TEXT NOT NULL,
    "prediction_template" TEXT NOT NULL,
    "confidence_base" INTEGER DEFAULT 50,
    "life_areas" TEXT,
    "timing_advice" TEXT,
    "colors" TEXT,
    "is_active" TEXT DEFAULT 'TRUE',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "house_specifications" CASCADE;
CREATE TABLE "house_specifications" (
    "id" SERIAL,
    "house_number" INTEGER NOT NULL,
    "specifications" TEXT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "house_combinations" CASCADE;
CREATE TABLE "house_combinations" (
    "id" SERIAL,
    "houses" TEXT NOT NULL,
    "positive_prediction" TEXT NOT NULL,
    "negative_prediction" TEXT NOT NULL,
    "combination_name" TEXT NOT NULL,
    "is_active" TEXT DEFAULT 'TRUE',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "nakshatras" CASCADE;
CREATE TABLE "nakshatras" (
    "id" SERIAL,
    "name" TEXT NOT NULL,
    "lord" TEXT NOT NULL,
    "deity" TEXT NOT NULL,
    "nature" TEXT NOT NULL,
    "guna" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "characteristics" TEXT NOT NULL,
    "positive_traits" TEXT NOT NULL,
    "negative_traits" TEXT NOT NULL,
    "careers" TEXT NOT NULL,
    "compatibility" TEXT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "subscription_plans" CASCADE;
CREATE TABLE "subscription_plans" (
    "plan_id" INTEGER,
    "platform" TEXT NOT NULL,
    "plan_name" TEXT NOT NULL,
    "price" NUMERIC DEFAULT 0.00,
    "duration_months" INTEGER DEFAULT 1,
    "features" TEXT NOT NULL,
    "is_active" TEXT DEFAULT 'true',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "tier_name" TEXT,
    "discount_percent" INTEGER DEFAULT 0,
    "google_play_product_id" TEXT,
    PRIMARY KEY ("plan_id")
);

DROP TABLE IF EXISTS "ai_health_insights" CASCADE;
CREATE TABLE "ai_health_insights" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL DEFAULT 0,
    "birth_hash" TEXT NOT NULL,
    "insights_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userid", "birth_hash"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "chat_conversations" CASCADE;
CREATE TABLE "chat_conversations" (
    "id" SERIAL,
    "birth_hash" TEXT,
    "conversation_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "clarification_count" INTEGER DEFAULT 0,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "ai_wealth_insights" CASCADE;
CREATE TABLE "ai_wealth_insights" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL DEFAULT 0,
    "birth_hash" TEXT NOT NULL,
    "insights_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userid", "birth_hash"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "credit_settings" CASCADE;
CREATE TABLE "credit_settings" (
    "id" SERIAL,
    "setting_key" TEXT NOT NULL,
    "setting_value" INTEGER NOT NULL,
    "description" TEXT,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "discount" INTEGER,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "ai_marriage_insights" CASCADE;
CREATE TABLE "ai_marriage_insights" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL DEFAULT 0,
    "birth_hash" TEXT NOT NULL,
    "insights_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userid", "birth_hash"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "ai_education_insights" CASCADE;
CREATE TABLE "ai_education_insights" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL DEFAULT 0,
    "birth_hash" TEXT NOT NULL,
    "insights_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userid", "birth_hash"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "ai_career_insights" CASCADE;
CREATE TABLE "ai_career_insights" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL DEFAULT 0,
    "birth_hash" TEXT NOT NULL,
    "insights_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userid", "birth_hash"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "analysis_pricing" CASCADE;
CREATE TABLE "analysis_pricing" (
    "id" SERIAL,
    "analysis_type" TEXT NOT NULL,
    "credits" INTEGER NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "trading_daily_cache" CASCADE;
CREATE TABLE "trading_daily_cache" (
    "id" SERIAL,
    "cache_key" TEXT,
    "user_id" INTEGER,
    "target_date" TEXT,
    "analysis_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "trading_monthly_cache" CASCADE;
CREATE TABLE "trading_monthly_cache" (
    "id" SERIAL,
    "cache_key" TEXT,
    "user_id" INTEGER,
    "year" INTEGER,
    "month" INTEGER,
    "analysis_data" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "physical_traits_cache" CASCADE;
CREATE TABLE "physical_traits_cache" (
    "id" SERIAL,
    "birth_chart_id" BIGINT NOT NULL,
    "traits_data" TEXT NOT NULL,
    "user_feedback" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "birth_charts_backup" CASCADE;
CREATE TABLE "birth_charts_backup" (
    "id" INTEGER,
    "userid" INTEGER,
    "name" TEXT,
    "date" TEXT,
    "time" TEXT,
    "latitude" TEXT,
    "longitude" TEXT,
    "timezone" TEXT,
    "created_at" TEXT,
    "place" TEXT,
    "gender" TEXT,
    "relation" TEXT,
    "is_rectified" INTEGER,
    "calibration_year" INTEGER
);

DROP TABLE IF EXISTS "market_forecast_periods" CASCADE;
CREATE TABLE "market_forecast_periods" (
    "id" SERIAL,
    "sector" TEXT NOT NULL,
    "ruler" TEXT NOT NULL,
    "start_date" TIMESTAMP NOT NULL,
    "end_date" TIMESTAMP NOT NULL,
    "trend" TEXT NOT NULL,
    "intensity" TEXT NOT NULL,
    "reason" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "market_forecast_metadata" CASCADE;
CREATE TABLE "market_forecast_metadata" (
    "id" SERIAL,
    "start_year" INTEGER,
    "end_year" INTEGER,
    "generated_at" TIMESTAMP,
    "total_periods" INTEGER,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "message_deletion_audit" CASCADE;
CREATE TABLE "message_deletion_audit" (
    "audit_id" INTEGER,
    "message_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "session_id" TEXT NOT NULL,
    "message_content" TEXT,
    "message_type" TEXT,
    "sender" TEXT,
    "deleted_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "deleted_by_ip" TEXT,
    PRIMARY KEY ("audit_id")
);

DROP TABLE IF EXISTS "blog_posts" CASCADE;
CREATE TABLE "blog_posts" (
    "id" SERIAL,
    "title" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "excerpt" TEXT,
    "meta_description" TEXT,
    "tags" TEXT,
    "category" TEXT,
    "author" TEXT DEFAULT 'AstroRoshni',
    "status" TEXT DEFAULT 'draft',
    "featured_image" TEXT,
    "view_count" INTEGER DEFAULT 0,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "published_at" TIMESTAMP,
    "scheduled_for" TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "blog_media" CASCADE;
CREATE TABLE "blog_media" (
    "id" SERIAL,
    "filename" TEXT NOT NULL,
    "gcs_path" TEXT NOT NULL,
    "public_url" TEXT NOT NULL,
    "original_name" TEXT,
    "file_size" INTEGER,
    "mime_type" TEXT,
    "alt_text" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "admin_settings" CASCADE;
CREATE TABLE "admin_settings" (
    "key" TEXT,
    "value" TEXT,
    "description" TEXT,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("key")
);

DROP TABLE IF EXISTS "karma_insights" CASCADE;
CREATE TABLE "karma_insights" (
    "id" SERIAL,
    "chart_id" TEXT NOT NULL,
    "user_id" INTEGER NOT NULL,
    "status" TEXT DEFAULT 'processing',
    "karma_context" TEXT,
    "ai_interpretation" TEXT,
    "sections" TEXT,
    "error" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "chat_error_logs" CASCADE;
CREATE TABLE "chat_error_logs" (
    "id" SERIAL,
    "user_id" INTEGER,
    "username" TEXT,
    "phone" TEXT,
    "error_type" TEXT,
    "error_message" TEXT,
    "user_question" TEXT,
    "stack_trace" TEXT,
    "platform" TEXT,
    "error_source" TEXT DEFAULT 'backend',
    "birth_data_context" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "prompt_instruction_modules" CASCADE;
CREATE TABLE "prompt_instruction_modules" (
    "id" SERIAL,
    "module_key" TEXT NOT NULL,
    "module_name" TEXT NOT NULL,
    "instruction_text" TEXT NOT NULL,
    "character_count" INTEGER,
    "is_active" TEXT DEFAULT 1,
    "priority" INTEGER DEFAULT 0,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "prompt_performance_log" CASCADE;
CREATE TABLE "prompt_performance_log" (
    "id" SERIAL,
    "category_key" TEXT,
    "instruction_size" INTEGER,
    "context_size" INTEGER,
    "total_prompt_size" INTEGER,
    "response_time_seconds" DOUBLE PRECISION,
    "success" TEXT,
    "error_message" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "astrological_layers" CASCADE;
CREATE TABLE "astrological_layers" (
    "layer_id" INTEGER,
    "layer_key" TEXT NOT NULL,
    "layer_name" TEXT NOT NULL,
    "description" TEXT,
    "priority" INTEGER DEFAULT 0,
    "is_active" TEXT DEFAULT 1,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("layer_id")
);

DROP TABLE IF EXISTS "divisional_charts" CASCADE;
CREATE TABLE "divisional_charts" (
    "chart_id" INTEGER,
    "chart_key" TEXT NOT NULL,
    "chart_name" TEXT NOT NULL,
    "chart_number" INTEGER,
    "primary_domain" TEXT,
    "description" TEXT,
    "estimated_size_bytes" INTEGER DEFAULT 3000,
    "is_active" TEXT DEFAULT 1,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("chart_id")
);

DROP TABLE IF EXISTS "prompt_tiers" CASCADE;
CREATE TABLE "prompt_tiers" (
    "id" SERIAL,
    "tier_key" TEXT NOT NULL,
    "tier_name" TEXT NOT NULL,
    "description" TEXT,
    "max_instruction_size" INTEGER,
    "max_context_size" INTEGER,
    "priority" INTEGER DEFAULT 0,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "prompt_category_config" CASCADE;
CREATE TABLE "prompt_category_config" (
    "id" SERIAL,
    "category_key" TEXT NOT NULL,
    "tier_key" TEXT NOT NULL DEFAULT 'normal',
    "category_name" TEXT NOT NULL,
    "required_modules" TEXT NOT NULL,
    "required_data_fields" TEXT NOT NULL,
    "optional_data_fields" TEXT,
    "max_transit_activations" INTEGER DEFAULT 20,
    "is_active" TEXT DEFAULT 1,
    "tier_context_config" TEXT DEFAULT '{}',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "category_transit_limits" CASCADE;
CREATE TABLE "category_transit_limits" (
    "limit_id" INTEGER,
    "category_key" TEXT NOT NULL,
    "tier_key" TEXT NOT NULL DEFAULT 'normal',
    "max_transit_activations" INTEGER DEFAULT 20,
    "include_macro_transits" TEXT DEFAULT 1,
    "include_navatara_warnings" TEXT DEFAULT 0,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("limit_id")
);

DROP TABLE IF EXISTS "device_tokens" CASCADE;
CREATE TABLE "device_tokens" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "token" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "nudge_deliveries" CASCADE;
CREATE TABLE "nudge_deliveries" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "trigger_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "event_params" TEXT,
    "sent_at" TIMESTAMP NOT NULL,
    "channel" TEXT DEFAULT 'stored',
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "glossary_terms" CASCADE;
CREATE TABLE "glossary_terms" (
    "term_id" TEXT,
    "display_text" TEXT NOT NULL,
    "definition" TEXT NOT NULL,
    "language" TEXT DEFAULT 'english',
    "aliases" TEXT,
    PRIMARY KEY ("term_id")
);

DROP TABLE IF EXISTS "reddit_questions" CASCADE;
CREATE TABLE "reddit_questions" (
    "id" SERIAL,
    "reddit_id" TEXT NOT NULL,
    "subreddit" TEXT NOT NULL,
    "title" TEXT,
    "body" TEXT,
    "url" TEXT,
    "author" TEXT,
    "created_utc" DOUBLE PRECISION,
    "has_birth_data" INTEGER DEFAULT 0,
    "extracted_birth_data" TEXT,
    "status" TEXT DEFAULT 'collected',
    "notes" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "admin_allowed_devices" CASCADE;
CREATE TABLE "admin_allowed_devices" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "device_id" TEXT NOT NULL,
    "label" TEXT,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "podcast_history" CASCADE;
CREATE TABLE "podcast_history" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "message_id" TEXT NOT NULL,
    "session_id" TEXT,
    "lang" TEXT NOT NULL DEFAULT 'en',
    "preview" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userid", "message_id", "lang"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "credit_transactions" CASCADE;
CREATE TABLE "credit_transactions" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "transaction_type" TEXT NOT NULL,
    "amount" INTEGER NOT NULL,
    "balance_after" INTEGER NOT NULL,
    "source" TEXT NOT NULL,
    "reference_id" TEXT,
    "description" TEXT,
    "metadata" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("userid") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "promo_codes" CASCADE;
CREATE TABLE "promo_codes" (
    "id" SERIAL,
    "code" TEXT NOT NULL,
    "credits" INTEGER NOT NULL,
    "max_uses" INTEGER DEFAULT 1,
    "used_count" INTEGER DEFAULT 0,
    "is_active" TEXT DEFAULT 'TRUE',
    "expires_at" TIMESTAMP,
    "created_by" INTEGER,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "max_uses_per_user" INTEGER DEFAULT 1,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("created_by") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "chat_sessions" CASCADE;
CREATE TABLE "chat_sessions" (
    "session_id" TEXT,
    "user_id" INTEGER NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- SQLite source data stores this sometimes as very large numeric floats,
    -- so BIGINT avoids integer overflow during migration.
    "birth_chart_id" BIGINT,
    PRIMARY KEY ("session_id"),
    FOREIGN KEY ("user_id") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "user_credits" CASCADE;
CREATE TABLE "user_credits" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "credits" INTEGER DEFAULT 0,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "free_chat_question_used" INTEGER DEFAULT 0,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("userid") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "user_settings" CASCADE;
CREATE TABLE "user_settings" (
    "id" SERIAL,
    "user_id" INTEGER NOT NULL,
    "setting_key" TEXT NOT NULL,
    "setting_value" TEXT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("user_id") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "birth_charts" CASCADE;
CREATE TABLE "birth_charts" (
    "id" BIGSERIAL,
    "userid" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "time" TEXT NOT NULL,
    "latitude" TEXT NOT NULL,
    "longitude" TEXT NOT NULL,
    "timezone" TEXT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "place" TEXT DEFAULT '',
    "gender" TEXT DEFAULT '',
    "relation" TEXT DEFAULT 'other',
    "is_rectified" INTEGER DEFAULT 0,
    "calibration_year" INTEGER,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("userid") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "credit_requests" CASCADE;
CREATE TABLE "credit_requests" (
    "id" SERIAL,
    "userid" INTEGER NOT NULL,
    "requested_amount" INTEGER NOT NULL,
    "reason" TEXT NOT NULL,
    "status" TEXT DEFAULT 'pending',
    "admin_notes" TEXT,
    "approved_amount" INTEGER,
    "approved_by" INTEGER,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("approved_by") REFERENCES "users" ("userid"),
    FOREIGN KEY ("userid") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "user_subscriptions" CASCADE;
CREATE TABLE "user_subscriptions" (
    "id" SERIAL,
    -- Legacy SQLite primary key retained for migration compatibility
    "subscription_id" INTEGER,
    "userid" INTEGER NOT NULL,
    "plan_id" INTEGER NOT NULL,
    "status" TEXT DEFAULT 'active',
    "start_date" TIMESTAMP NOT NULL,
    "end_date" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    UNIQUE ("subscription_id"),
    FOREIGN KEY ("plan_id") REFERENCES "subscription_plans" ("plan_id"),
    FOREIGN KEY ("userid") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "context_fields" CASCADE;
CREATE TABLE "context_fields" (
    "field_id" INTEGER,
    "field_key" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "description" TEXT,
    "estimated_size_bytes" INTEGER,
    "layer_id" INTEGER,
    "is_active" TEXT DEFAULT 1,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("field_id"),
    FOREIGN KEY ("layer_id") REFERENCES "astrological_layers" ("layer_id")
);

DROP TABLE IF EXISTS "category_layer_requirements" CASCADE;
CREATE TABLE "category_layer_requirements" (
    "requirement_id" INTEGER,
    "category_key" TEXT NOT NULL,
    "tier_key" TEXT NOT NULL DEFAULT 'normal',
    "layer_id" INTEGER NOT NULL,
    "is_required" TEXT DEFAULT 1,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("requirement_id"),
    FOREIGN KEY ("layer_id") REFERENCES "astrological_layers" ("layer_id")
);

DROP TABLE IF EXISTS "category_divisional_requirements" CASCADE;
CREATE TABLE "category_divisional_requirements" (
    "requirement_id" INTEGER,
    "category_key" TEXT NOT NULL,
    "tier_key" TEXT NOT NULL DEFAULT 'normal',
    "chart_id" INTEGER NOT NULL,
    "is_required" TEXT DEFAULT 1,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("requirement_id"),
    FOREIGN KEY ("chart_id") REFERENCES "divisional_charts" ("chart_id")
);

DROP TABLE IF EXISTS "reddit_answers" CASCADE;
CREATE TABLE "reddit_answers" (
    "id" SERIAL,
    "question_id" INTEGER NOT NULL,
    "draft_markdown" TEXT,
    "safety_flags" TEXT,
    "status" TEXT DEFAULT 'draft',
    "reviewed_by" TEXT,
    "reviewed_at" TIMESTAMP,
    "posted_at" TIMESTAMP,
    "reddit_comment_id" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("question_id") REFERENCES "reddit_questions" ("id")
);

DROP TABLE IF EXISTS "promo_code_usage" CASCADE;
CREATE TABLE "promo_code_usage" (
    "id" SERIAL,
    "promo_code_id" INTEGER NOT NULL,
    "userid" INTEGER NOT NULL,
    "credits_earned" INTEGER NOT NULL,
    "used_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("userid") REFERENCES "users" ("userid"),
    FOREIGN KEY ("promo_code_id") REFERENCES "promo_codes" ("id")
);

DROP TABLE IF EXISTS "conversation_state" CASCADE;
CREATE TABLE "conversation_state" (
    "session_id" TEXT,
    "clarification_count" INTEGER DEFAULT 0,
    "extracted_context" TEXT,
    "last_updated" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("session_id"),
    FOREIGN KEY ("session_id") REFERENCES "chat_sessions" ("session_id")
);

DROP TABLE IF EXISTS "chat_messages" CASCADE;
CREATE TABLE "chat_messages" (
    "message_id" SERIAL,
    "session_id" TEXT NOT NULL,
    "sender" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "status" TEXT DEFAULT 'completed',
    "started_at" TIMESTAMP,
    "completed_at" TIMESTAMP,
    "error_message" TEXT,
    "message_type" TEXT DEFAULT 'answer',
    "terms" TEXT,
    "glossary" TEXT,
    "images" TEXT,
    "follow_up_questions" TEXT,
    "category" TEXT,
    "canonical_question" TEXT,
    "categorized_at" TIMESTAMP,
    "language" TEXT,
    "intent_router_ms" DOUBLE PRECISION,
    "client_request_id" TEXT,
    PRIMARY KEY ("message_id"),
    FOREIGN KEY ("session_id") REFERENCES "chat_sessions" ("session_id")
);

DROP TABLE IF EXISTS "user_facts" CASCADE;
CREATE TABLE "user_facts" (
    "id" SERIAL,
    "birth_chart_id" BIGINT NOT NULL,
    "category" TEXT NOT NULL,
    "fact" TEXT NOT NULL,
    "confidence" DOUBLE PRECISION DEFAULT 1.0,
    "extracted_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("birth_chart_id") REFERENCES "birth_charts" ("id")
);

DROP TABLE IF EXISTS "event_timeline_jobs" CASCADE;
CREATE TABLE "event_timeline_jobs" (
    "job_id" TEXT,
    "user_id" INTEGER NOT NULL,
    "birth_chart_id" BIGINT NOT NULL,
    "selected_year" INTEGER NOT NULL,
    "status" TEXT DEFAULT 'pending',
    "result_data" TEXT,
    "error_message" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "started_at" TIMESTAMP,
    "completed_at" TIMESTAMP,
    "selected_month" INTEGER,
    PRIMARY KEY ("job_id"),
    FOREIGN KEY ("birth_chart_id") REFERENCES "birth_charts" ("id"),
    FOREIGN KEY ("user_id") REFERENCES "users" ("userid")
);

DROP TABLE IF EXISTS "message_feedback" CASCADE;
CREATE TABLE "message_feedback" (
    "id" SERIAL,
    "message_id" INTEGER NOT NULL,
    "rating" INTEGER NOT NULL,
    "comment" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("message_id") REFERENCES "chat_messages" ("message_id") ON DELETE CASCADE
);


-- Indexes

CREATE INDEX idx_sessions_user_id ON chat_sessions (user_id);

CREATE INDEX idx_sessions_created_at ON chat_sessions (created_at);

CREATE INDEX idx_messages_session_id ON chat_messages (session_id);

CREATE INDEX idx_messages_status ON chat_messages (status);

CREATE INDEX idx_timeline_user_id ON event_timeline_jobs (user_id);

CREATE INDEX idx_timeline_birth_chart ON event_timeline_jobs (birth_chart_id);

CREATE INDEX idx_timeline_status ON event_timeline_jobs (status);

CREATE INDEX idx_sessions_birth_chart ON chat_sessions (birth_chart_id);

CREATE INDEX idx_user_facts_birth_chart ON user_facts (birth_chart_id);

CREATE INDEX idx_user_facts_category ON user_facts (category);

CREATE INDEX idx_sector_date ON market_forecast_periods(sector, start_date, end_date);

CREATE INDEX idx_blog_posts_status ON blog_posts(status);

CREATE INDEX idx_blog_posts_published ON blog_posts(published_at DESC);

CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);

CREATE INDEX idx_module_key ON prompt_instruction_modules(module_key);

CREATE INDEX idx_perf_category ON prompt_performance_log(category_key);

CREATE INDEX idx_perf_created ON prompt_performance_log(created_at);

CREATE INDEX idx_category_key ON prompt_category_config(category_key);

CREATE INDEX idx_nudge_deliveries_user_sent ON nudge_deliveries(userid, sent_at);

CREATE INDEX idx_podcast_history_userid ON podcast_history(userid);

CREATE INDEX idx_podcast_history_created_at ON podcast_history(created_at DESC);
