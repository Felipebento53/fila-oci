import json
import os
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from services.oci_queue import OCIQueueService
from services.database import init_db, log_event, recent_events, metrics

load_dotenv(BASE_DIR / ".env")
app = Flask(__name__, template_folder="templates", static_folder=str(BASE_DIR / "static"))
init_db()

state = {
    "running": True,
    "connected": False,
    "last_error": "",
    "last_poll": None
}

def consumer_loop():
    poll_pause = float(os.getenv("CONSUMER_POLL_SECONDS", "3"))
    visibility = int(os.getenv("CONSUMER_VISIBILITY_SECONDS", "30"))
    timeout = int(os.getenv("CONSUMER_LONG_POLL_SECONDS", "10"))
    limit = int(os.getenv("CONSUMER_BATCH_SIZE", "10"))

    while True:
        if not state["running"]:
            time.sleep(1)
            continue

        try:
            service = OCIQueueService()
            state["connected"] = True
            state["last_error"] = ""
            state["last_poll"] = time.strftime("%H:%M:%S")

            messages = service.receive(limit=limit, visibility=visibility, timeout=timeout)

            for message in messages:
                try:
                    payload = json.loads(message.content)
                    order_id = payload.get("id", "SEM-ID")
                    delivery_count = getattr(message, "delivery_count", None)
                    log_event(order_id, "RECEBIDO", f"delivery_count={delivery_count}")

                    # Falha proposital: não apagamos a mensagem.
                    # Após o visibility timeout ela poderá ser entregue novamente.
                    if payload.get("simular_erro"):
                        log_event(order_id, "ERRO", "Falha simulada; mensagem não confirmada.")
                        continue

                    # Aqui entraria a regra de negócio real.
                    time.sleep(0.5)

                    service.delete(message.receipt)
                    log_event(order_id, "PROCESSADO", "Pedido processado e mensagem removida da fila.")
                except Exception as exc:
                    log_event(
                        getattr(message, "id", "DESCONHECIDO"),
                        "ERRO",
                        f"Erro ao processar mensagem: {exc}"
                    )

        except Exception as exc:
            state["connected"] = False
            state["last_error"] = str(exc)
            time.sleep(poll_pause)

@app.get("/")
def dashboard():
    return render_template(
        "consumer.html",
        events=recent_events(30),
        metrics=metrics(),
        state=state
    )

@app.post("/api/toggle")
def toggle():
    state["running"] = not state["running"]
    return jsonify(state)

@app.get("/api/status")
def status():
    return jsonify({"metrics": metrics(), "events": recent_events(30), "state": state})

if __name__ == "__main__":
    threading.Thread(target=consumer_loop, daemon=True).start()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("CONSUMER_PORT", "5001")),
        debug=True,
        use_reloader=False
    )
