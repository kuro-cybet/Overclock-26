-- Migration: 20261031040000_whatsapp_and_profile_extensions.sql
-- Description: Adds WhatsApp integration tables, session/conversation state, and user/report schema extensions
-- Target: Supabase PostgreSQL (Public Schema)

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. Alter Users Table: Add Phone, WhatsApp Verification, and Auth Extension Fields
-- -----------------------------------------------------------------------------
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS phone_number character varying(30),
    ADD COLUMN IF NOT EXISTS whatsapp_verified boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS auth_provider character varying(20) DEFAULT 'password',
    ADD COLUMN IF NOT EXISTS provider_subject character varying(255),
    ADD COLUMN IF NOT EXISTS email_verified boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS last_login_at timestamp without time zone;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_users_phone_number'
    ) THEN
        ALTER TABLE public.users ADD CONSTRAINT uq_users_phone_number UNIQUE (phone_number);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_phone_number ON public.users (phone_number);
CREATE INDEX IF NOT EXISTS idx_users_provider_subject ON public.users (provider_subject);

-- -----------------------------------------------------------------------------
-- 2. Alter Reports Table: Add Contact Phone
-- -----------------------------------------------------------------------------
ALTER TABLE public.reports
    ADD COLUMN IF NOT EXISTS contact_phone character varying(30);

CREATE INDEX IF NOT EXISTS idx_reports_contact_phone ON public.reports (contact_phone);

-- -----------------------------------------------------------------------------
-- 3. Alter Notification Outbox Table: Add WhatsApp Delivery & Idempotency Fields
-- -----------------------------------------------------------------------------
ALTER TABLE public.notification_outbox
    ADD COLUMN IF NOT EXISTS recipient_phone character varying(50),
    ADD COLUMN IF NOT EXISTS event_type character varying(50),
    ADD COLUMN IF NOT EXISTS idempotency_key character varying(128);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_notification_outbox_idempotency_key'
    ) THEN
        ALTER TABLE public.notification_outbox ADD CONSTRAINT uq_notification_outbox_idempotency_key UNIQUE (idempotency_key);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_notification_outbox_recipient_phone ON public.notification_outbox (recipient_phone);
CREATE INDEX IF NOT EXISTS idx_notification_outbox_idempotency_key ON public.notification_outbox (idempotency_key);

-- -----------------------------------------------------------------------------
-- 4. Create Table: whatsapp_user_links
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.whatsapp_user_links (
    id character varying(36) PRIMARY KEY,
    user_id character varying(36) NOT NULL,
    phone_number character varying(30) NOT NULL UNIQUE,
    verification_code character varying(10),
    code_expires_at timestamp without time zone,
    is_verified boolean NOT NULL DEFAULT false,
    verified_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wa_user_links_user FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wa_user_links_user_id ON public.whatsapp_user_links (user_id);
CREATE INDEX IF NOT EXISTS idx_wa_user_links_phone_number ON public.whatsapp_user_links (phone_number);

-- -----------------------------------------------------------------------------
-- 5. Create Table: whatsapp_conversations (Authoritative multi-turn state)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.whatsapp_conversations (
    id character varying(36) PRIMARY KEY,
    phone_number character varying(30) NOT NULL UNIQUE,
    user_id character varying(36),
    state character varying(50) NOT NULL DEFAULT 'idle',
    current_intent character varying(50),
    extracted_data_json text,
    last_message_id character varying(100),
    last_interaction_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wa_conv_user FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_wa_convs_phone ON public.whatsapp_conversations (phone_number);
CREATE INDEX IF NOT EXISTS idx_wa_convs_user_id ON public.whatsapp_conversations (user_id);

-- -----------------------------------------------------------------------------
-- 6. Create Table: whatsapp_sessions (Legacy compatibility)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.whatsapp_sessions (
    id character varying(36) PRIMARY KEY,
    phone_number character varying(30) NOT NULL UNIQUE,
    user_id character varying(36),
    current_intent character varying(50),
    step character varying(50) NOT NULL DEFAULT 'IDLE',
    context_data text NOT NULL DEFAULT '{}',
    last_active_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wa_session_user FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_wa_sessions_phone ON public.whatsapp_sessions (phone_number);
CREATE INDEX IF NOT EXISTS idx_wa_sessions_user_id ON public.whatsapp_sessions (user_id);

-- -----------------------------------------------------------------------------
-- 7. Create Table: whatsapp_messages_log (Idempotent audit log)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.whatsapp_messages_log (
    id character varying(36) PRIMARY KEY,
    message_id character varying(100) NOT NULL UNIQUE,
    sender_phone character varying(30) NOT NULL,
    recipient_phone character varying(30) NOT NULL,
    direction character varying(10) NOT NULL,
    message_type character varying(20) NOT NULL DEFAULT 'text',
    content text NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'received',
    error_details text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wa_msgs_message_id ON public.whatsapp_messages_log (message_id);
CREATE INDEX IF NOT EXISTS idx_wa_msgs_sender ON public.whatsapp_messages_log (sender_phone);
CREATE INDEX IF NOT EXISTS idx_wa_msgs_recipient ON public.whatsapp_messages_log (recipient_phone);

COMMIT;

-- =============================================================================
-- ROLLBACK / DOWN MIGRATION (Execute manually if rollback is required)
-- =============================================================================
/*
BEGIN;
DROP TABLE IF EXISTS public.whatsapp_messages_log;
DROP TABLE IF EXISTS public.whatsapp_sessions;
DROP TABLE IF EXISTS public.whatsapp_conversations;
DROP TABLE IF EXISTS public.whatsapp_user_links;

ALTER TABLE public.notification_outbox
    DROP CONSTRAINT IF EXISTS uq_notification_outbox_idempotency_key,
    DROP COLUMN IF EXISTS idempotency_key,
    DROP COLUMN IF EXISTS event_type,
    DROP COLUMN IF EXISTS recipient_phone;

ALTER TABLE public.reports
    DROP COLUMN IF EXISTS contact_phone;

ALTER TABLE public.users
    DROP CONSTRAINT IF EXISTS uq_users_phone_number,
    DROP COLUMN IF EXISTS last_login_at,
    DROP COLUMN IF EXISTS email_verified,
    DROP COLUMN IF EXISTS provider_subject,
    DROP COLUMN IF EXISTS auth_provider,
    DROP COLUMN IF EXISTS whatsapp_verified,
    DROP COLUMN IF EXISTS phone_number;
COMMIT;
*/

