BEGIN;

ALTER TABLE public.notification_outbox
    ADD COLUMN IF NOT EXISTS event_type character varying(50);

UPDATE public.notification_outbox
SET event_type = 'legacy'
WHERE event_type IS NULL
  AND channel = 'email';

COMMIT;
