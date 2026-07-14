#!/usr/bin/env python3
"""
Brevo Email Automation - Render Deployment
Monitora Lista 2 e dispara sequência de 6 emails com delays automáticos
+ Notificação de vendas/problemas por email e SMS
"""

import requests
import time
from datetime import datetime, timedelta
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Ler chave da variável de ambiente
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
if not BREVO_API_KEY:
    raise ValueError("BREVO_API_KEY environment variable not set")

BREVO_API_URL = "https://api.brevo.com/v3"
LIST_ID = 2
RAFAEL_EMAIL = "rafaeloliveiragomes0@gmail.com"

# Template IDs para sequência de 6 emails
EMAILS = {
    1: {"template_id": 7, "delay_days": 0, "name": "Prompt Pack"},
    2: {"template_id": 8, "delay_days": 2, "name": "Prompt Chaining"},
    3: {"template_id": 9, "delay_days": 2, "name": "Blueprint $27"},
    4: {"template_id": 10, "delay_days": 3, "name": "Marketing $47"},
    5: {"template_id": 11, "delay_days": 3, "name": "E-commerce $67"},
    6: {"template_id": 12, "delay_days": 4, "name": "Freelancers $97"},
}

# Template IDs para notificações (venda/problema)
NOTIFICATION_TEMPLATES = {
    "sale": 13,        # Template ID 13 - Notificação de Venda
    "problem": 14,     # Template ID 14 - Notificação de Problema
}

headers = {"api-key": BREVO_API_KEY, "Content-Type": "application/json"}
tracked_contacts = {}

# ==================== ENDPOINTS HEALTH ====================
@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}, 200

@app.route('/status', methods=['GET'])
def status():
    return {
        "status": "running",
        "contacts_tracked": len(tracked_contacts),
        "timestamp": datetime.now().isoformat()
    }, 200

# ==================== ENDPOINT DE VENDA ====================
@app.route('/webhook/sale', methods=['POST'])
def webhook_sale():
    """
    Recebe notificação de venda
    POST /webhook/sale
    {
        "customer_email": "customer@example.com",
        "customer_name": "Nome do Cliente",
        "product_name": "Nome do Produto",
        "amount": 27.00,
        "order_id": "12345"
    }
    """
    try:
        data = request.get_json()
        customer_email = data.get("customer_email", "")
        customer_name = data.get("customer_name", "")
        product_name = data.get("product_name", "")
        amount = data.get("amount", 0)
        order_id = data.get("order_id", "")
        
        # Enviar email de notificação para Rafael
        notification_message = f"""
        Nova Venda!
        
        Cliente: {customer_name}
        Email: {customer_email}
        Produto: {product_name}
        Valor: R$ {amount}
        Pedido ID: {order_id}
        Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        send_notification_email(
            RAFAEL_EMAIL,
            f"🎉 VENDA REALIZADA - {product_name}",
            notification_message,
            "sale"
        )
        
        # Log
        print(f"✅ VENDA NOTIFICADA: {customer_name} - R${amount} - {order_id}")
        
        return {
            "status": "success",
            "message": "Venda registrada e notificação enviada",
            "order_id": order_id
        }, 200
        
    except Exception as e:
        print(f"❌ Erro ao processar venda: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

# ==================== ENDPOINT DE PROBLEMA ====================
@app.route('/webhook/problem', methods=['POST'])
def webhook_problem():
    """
    Recebe notificação de problema/erro
    POST /webhook/problem
    {
        "problem_type": "payment_failed",
        "description": "Descrição do problema",
        "severity": "high",
        "customer_email": "customer@example.com",
        "order_id": "12345"
    }
    """
    try:
        data = request.get_json()
        problem_type = data.get("problem_type", "")
        description = data.get("description", "")
        severity = data.get("severity", "medium")
        customer_email = data.get("customer_email", "")
        order_id = data.get("order_id", "")
        
        # Enviar email de notificação para Rafael
        notification_message = f"""
        ⚠️ PROBLEMA DETECTADO!
        
        Tipo: {problem_type}
        Severidade: {severity}
        Descrição: {description}
        Cliente/Pedido: {customer_email} ({order_id})
        Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        send_notification_email(
            RAFAEL_EMAIL,
            f"⚠️ PROBLEMA - {problem_type.upper()} [{severity.upper()}]",
            notification_message,
            "problem"
        )
        
        # Log
        print(f"⚠️ PROBLEMA NOTIFICADO: {problem_type} - Severidade: {severity}")
        
        return {
            "status": "success",
            "message": "Problema registrado e notificação enviada"
        }, 200
        
    except Exception as e:
        print(f"❌ Erro ao processar problema: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

# ==================== FUNÇÕES DE EMAIL ====================
def send_email(email, template_id, name=""):
    try:
        url = f"{BREVO_API_URL}/smtp/email"
        payload = {
            "to": [{"email": email, "name": name}],
            "templateId": template_id,
            "params": {"FNAME": name.split()[0] if name else "Visitante"}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.status_code == 201
    except:
        return False

def send_notification_email(email, subject, message, notification_type="sale"):
    """Envia email de notificação (venda/problema)"""
    try:
        url = f"{BREVO_API_URL}/smtp/email"
        
        # Se houver um template específico, usar; senão, usar email genérico
        template_id = NOTIFICATION_TEMPLATES.get(notification_type)
        
        if template_id:
            # Com template
            payload = {
                "to": [{"email": email, "name": "Rafael"}],
                "templateId": template_id,
                "params": {
                    "MESSAGE": message,
                    "SUBJECT": subject
                }
            }
        else:
            # Sem template - email direto
            payload = {
                "to": [{"email": email, "name": "Rafael"}],
                "subject": subject,
                "htmlContent": f"<pre>{message}</pre>"
            }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        success = response.status_code in [201, 200]
        
        if success:
            print(f"✅ Notificação enviada para {email}")
        else:
            print(f"❌ Erro ao enviar notificação: {response.status_code}")
        
        return success
    except Exception as e:
        print(f"❌ Erro ao enviar notificação: {str(e)}")
        return False

# ==================== FUNÇÕES DE CONTATO ====================
def get_contacts_from_list():
    try:
        url = f"{BREVO_API_URL}/contacts/lists/{LIST_ID}/contacts"
        response = requests.get(url, headers=headers, params={"limit": 1000}, timeout=10)
        return response.json().get("contacts", []) if response.status_code == 200 else []
    except:
        return []

def track_contact(contact_id, email, name=""):
    if email not in tracked_contacts:
        tracked_contacts[email] = {
            "id": contact_id,
            "name": name,
            "added_date": datetime.now(),
            "sent": {},
            "status": "Aguardando Email 1"
        }
        print(f"📝 Novo contato rastreado: {email}")
        return True
    return False

# ==================== PROCESSAMENTO DE SEQUÊNCIA ====================
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
        except Exception as e:
            print(f"❌ Erro no monitor: {str(e)}")
            time.sleep(60)

# ==================== INICIALIZAÇÃO ====================
import threading
threading.Thread(target=monitor, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
