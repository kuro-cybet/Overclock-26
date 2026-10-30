import json
from datetime import datetime
from typing import Dict, Any

class WebhookSimulator:
    def send_webhook_payload(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "delivery_status": 200,
            "signature": f"sig_mock_{hash(json.dumps(data, default=str))}"
        }
        return payload

webhook_simulator = WebhookSimulator()

