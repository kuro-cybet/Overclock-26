import asyncio
import logging
from typing import Optional
from app.database.connection import SessionLocal
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

class OutboxWorker:
    def __init__(self, poll_interval_seconds: int = 5):
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self):
        """Starts the background worker task safely without blocking."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._worker_loop(), name="NotificationOutboxWorker")
        logger.info(f"[OutboxWorker] Started background outbox worker with {self.poll_interval}s interval.")

    async def stop(self):
        """Stops the background worker safely without blocking or dropping sessions."""
        if not self._running:
            return
        logger.info("[OutboxWorker] Stopping background outbox worker...")
        self._running = False
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        logger.info("[OutboxWorker] Background outbox worker stopped safely.")

    async def _worker_loop(self):
        while self._running:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._process_tick)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[OutboxWorker] Error during outbox tick: {e}", exc_info=True)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_interval)
                break
            except asyncio.TimeoutError:
                continue

    def _process_tick(self):
        db = SessionLocal()
        try:
            notification_service.process_pending_outbox(db=db, max_items=25)
        except Exception as e:
            logger.error(f"[OutboxWorker] Exception in outbox processing: {e}")
        finally:
            db.close()

outbox_worker = OutboxWorker(poll_interval_seconds=5)

