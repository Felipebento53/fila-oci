import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from services.oci_queue import OCIQueueService
from services.database import init_db, log_event, recent_events, metrics

load_dotenv(BASE_DIR / ".env")
app = Flask(__name__, template_folder="templates", static_folder=str(BASE_DIR / "static"))
app.secret_key = "oci-queue-demo"
init_db()

@app.get("/")
def index():
    return render_template("producer.html", events=recent_events(12), metrics=metrics())

@app.post("/pedido")
def create_order():
    cliente = request.form.get("cliente", "").strip()
    produto = request.form.get("produto", "").strip()
    quantidade = request.form.get("quantidade", type=int)
    prioridade = request.form.get("prioridade", "normal")
    simular_erro = request.form.get("simular_erro") == "on"

    if not cliente or not produto or not quantidade or quantidade < 1:
        flash("Preencha cliente, produto e uma quantidade válida.", "error")
        return redirect(url_for("index"))

    order_id = f"PED-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "id": order_id,
        "cliente": cliente,
        "produto": produto,
        "quantidade": quantidade,
        "prioridade": prioridade,
        "simular_erro": simular_erro,
        "criado_em": datetime.now(timezone.utc).isoformat()
    }

    try:
        OCIQueueService().send(payload)
        log_event(order_id, "ENVIADO", f"{cliente} | {produto} | qtd={quantidade} | prioridade={prioridade}")
        flash(f"{order_id} enviado para a OCI Queue.", "success")
    except Exception as exc:
        log_event(order_id, "FALHA_ENVIO", str(exc))
        flash(f"Falha ao enviar: {exc}", "error")

    return redirect(url_for("index"))

@app.get("/api/status")
def api_status():
    return jsonify({"metrics": metrics(), "events": recent_events(12)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PRODUCER_PORT", "5000")), debug=True)
