import json
import os
from pathlib import Path
import oci
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

class OCIQueueService:
    def __init__(self):
        self.queue_id = os.getenv("OCI_QUEUE_ID", "").strip()
        self.endpoint = os.getenv("OCI_QUEUE_MESSAGES_ENDPOINT", "").strip()
        config_file = os.path.expanduser(os.getenv("OCI_CONFIG_FILE", "~/.oci/config"))
        profile = os.getenv("OCI_PROFILE", "DEFAULT")

        if not self.queue_id:
            raise RuntimeError("OCI_QUEUE_ID não configurado no .env.")
        if not self.endpoint:
            raise RuntimeError("OCI_QUEUE_MESSAGES_ENDPOINT não configurado no .env.")

        config = oci.config.from_file(config_file, profile)
        self.client = oci.queue.QueueClient(config, service_endpoint=self.endpoint)

    def send(self, payload: dict):
        content = json.dumps(payload, ensure_ascii=False)
        details = oci.queue.models.PutMessagesDetails(
            messages=[
                oci.queue.models.PutMessagesDetailsEntry(
                    content=content,
                    metadata=oci.queue.models.MessageMetadata(
                        custom_properties={
                            "tipo": "pedido",
                            "prioridade": str(payload.get("prioridade", "normal"))
                        }
                    )
                )
            ]
        )
        response = self.client.put_messages(
            queue_id=self.queue_id,
            put_messages_details=details
        )
        return response.data

    def receive(self, limit=10, visibility=30, timeout=10):
        response = self.client.get_messages(
            queue_id=self.queue_id,
            limit=limit,
            visibility_in_seconds=visibility,
            timeout_in_seconds=timeout
        )
        return response.data.messages or []

    def delete(self, receipt: str):
        self.client.delete_message(
            queue_id=self.queue_id,
            message_receipt=receipt
        )

    def stats(self):
        return self.client.get_stats(queue_id=self.queue_id).data
