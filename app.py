#!/usr/bin/env python3
"""
Brevo Email Automation - Render Deployment
Monitora Lista 2 e dispara sequência de 6 emails com delays automáticos
"""

import requests
import time
from datetime import datetime, timedelta
import os
from flask import Flask

app = Flask(__name__)

# Ler chave da variável de ambiente
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
if not BREVO_API_KEY:
    raise ValueError("BREVO_API_KEY environment variable not set")

BREVO_API_URL = "https://api.brevo.com/v3"
LIST_ID = 2

EMAILS = {
    1: {"template_id": 7, "delay_days": 0, "name": "Prompt Pack"},
    2: {"template_id": 8, "delay_days": 2, "name": "Prompt Chaining"},
    3: {"template_id": 9, "delay_days": 2, "name": "Blueprint $27"},
    4: {"template_id": 10, "delay_days": 3, "name": "Marketing $47"},
    5: {"template_id": 11, "delay_days": 3, "name": "E-commerce $67"},
    6: {"template_id": 12, "delay_days": 4, "name": "Freelancers $97"},
}

headers = {"api-key": BREVO_API_KEY, "Content-Type": "application/json"}
tracked_contacts = {}

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}, 200

@app.route('/status', methods=['GET'])
def status():
    return {"status": "running", "contacts": len(tracked_contacts)}, 200

def get_contacts_from_list():
    try:
        url = f"{BREVO_API_URL}/contacts/lists/{LIST_ID}/contacts"
        response = requests.get(url, headers=headers, params={"limit": 1000}, timeout=10)
        return response.json().get("contacts", []) if response.status_code == 200 else []
    except:
        return []

def send_email(email, template_id, name=""):
    try:
        url = f"{BREVO_API_URL}/smtp/email"
        fname = name.split()[0] if name else "Visitante"
        payload = {
            "to": [{"email": email, "name": name}],
            "templateId": template_id,
            "params": {"FNAME": fname}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.status_code == 201
    except:
        return False

def track_contact(contact_id, email, name=""):
    if email not in tracked_contacts:
        tracked_contacts[email] = {
            "id": contact_id,
            "name": name,
            "added": datetime.now(),
            "sent": {},
            "status": "Aguardando Email 1"
        }
        return True
    return False

def process_sequence():
    now = datetime.now()
    for email, data in list(tracked_contacts.items()):
        if 1 not in data["sent"]:
            if send_email(email, EMAILS[1]["template_id"], data["name"]):
                data["sent"][1] = now
                data["status"] = "Email 1 Enviado"
        if 1 in data["sent"] and 2 not in data["sent"]:
            if now >= data["sent"][1] + timedelta(days=2):
                if send_email(email, EMAILS[2]["template_id"], data["name"]):
                    data["sent"][2] = now
                    data["status"] = "Email 2 Enviado"
        if 2 in data["sent"] and 3 not in data["sent"]:
            if now >= data["sent"][2] + timedelta(days=2):
                if send_email(email, EMAILS[3]["template_id"], data["name"]):
                    data["sent"][3] = now
                    data["status"] = "Email 3 Enviado"
        if 3 in data["sent"] and 4 not in data["sent"]:
            if now >= data["sent"][3] + timedelta(days=3):
                if send_email(email, EMAILS[4]["template_id"], data["name"]):
                    data["sent"][4] = now
                    data["status"] = "Email 4 Enviado"
        if 4 in data["sent"] and 5 not in data["sent"]:
            if now >= data["sent"][4] + timedelta(days=3):
                if send_email(email, EMAILS[5]["template_id"], data["name"]):
                    data["sent"][5] = now
                    data["status"] = "Email 5 Enviado"
        if 5 in data["sent"] and 6 not in data["sent"]:
            if now >= data["sent"][5] + timedelta(days=4):
                if send_email(email, EMAILS[6]["template_id"], data["name"]):
                    data["sent"][6] = now
                    data["status"] = "Sequência Completa"

def monitor():
    while True:
        try:
            contacts = get_contacts_from_list()
            for contact in contacts:
                email = contact.get("email", "")
                if email:
                    track_contact(contact.get("id"), email, contact.get("firstName", ""))
            process_sequence()
            time.sleep(300)
        except:
            time.sleep(60)

import threading
threading.Thread(target=monitor, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
