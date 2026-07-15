#!/usr/bin/env python3
import os
import json
import stripe
import requests
from flask import Flask, request

app = Flask(__name__)

# Carregar credenciais do ambiente
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

stripe.api_key = STRIPE_SECRET_KEY

# Mapeamento de preços para PDFs
PRICE_TO_PDF_MAPPING = {
    2700: "1_Ebook_AI_Income_Blueprint.pdf",
    4700: "2_Bonus_7_Essential_AI_Tools.pdf",
    6700: "3_Bonus_AI_Business_Launch_Workbook.pdf",
    9700: "4_Order_Bump_200_AI_Prompts.pdf"
}

# URLs dos PDFs no Cloudflare R2
PDF_URLS = {
    "1_Ebook_AI_Income_Blueprint.pdf": "https://r2.example.com/1_Ebook_AI_Income_Blueprint.pdf",
    "2_Bonus_7_Essential_AI_Tools.pdf": "https://r2.example.com/2_Bonus_7_Essential_AI_Tools.pdf",
    "3_Bonus_AI_Business_Launch_Workbook.pdf": "https://r2.example.com/3_Bonus_AI_Business_Launch_Workbook.pdf",
    "4_Order_Bump_200_AI_Prompts.pdf": "https://r2.example.com/4_Order_Bump_200_AI_Prompts.pdf"
}

def create_brevo_contact(email, name=None):
    """Criar contato no Brevo"""
    try:
        url = "https://api.brevo.com/v3/contacts"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        payload = {
            "email": email,
            "attributes": {"FIRSTNAME": name or "Customer"},
            "listIds": [2]  # Adicionar à lista padrão
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code in [201, 204]
    except Exception as e:
        print(f"Erro ao criar contato: {e}")
        return False

def send_brevo_email(email, name, pdf_filename):
    """Enviar email no Brevo com link do PDF"""
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        pdf_url = PDF_URLS.get(pdf_filename, "")
        
        payload = {
            "to": [{"email": email, "name": name or "Customer"}],
            "subject": "Seu Bônus AI Success Academy",
            "htmlContent": f"""
            <h1>Obrigado pela compra!</h1>
            <p>Aqui está seu bônus exclusivo:</p>
            <p><a href="{pdf_url}">Baixar seu PDF</a></p>
            """,
            "from": {"email": "noreply@aisuccessacademy.com", "name": "AI Success Academy"}
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code in [201, 202]
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Processar eventos do Stripe"""
    try:
        sig_header = request.headers.get("Stripe-Signature")
        event = stripe.Webhook.construct_event(
            request.get_data(), sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return {"status": "invalid signature"}, 400
    except stripe.error.SignatureVerificationError:
        return {"status": "invalid signature"}, 400
    
    # Processar evento charge.succeeded
    if event["type"] == "charge.succeeded":
        charge = event["data"]["object"]
        email = charge.get("receipt_email") or charge.get("billing_details", {}).get("email")
        name = charge.get("billing_details", {}).get("name", "Customer")
        amount = charge.get("amount", 0)
        
        if email:
            # Criar contato no Brevo
            create_brevo_contact(email, name)
            
            # Enviar email com PDF baseado no preço
            pdf = PRICE_TO_PDF_MAPPING.get(amount)
            if pdf:
                send_brevo_email(email, name, pdf)
    
    return {"status": "received"}, 200

@app.route("/api/price-to-pdf-mapping", methods=["GET"])
def get_mapping():
    return {"mapping": PRICE_TO_PDF_MAPPING}, 200

@app.route("/api/test-brevo", methods=["POST"])
def test_brevo():
    """Testar envio de email no Brevo"""
    try:
        email = request.json.get("email")
        name = request.json.get("name", "Test")
        create_brevo_contact(email, name)
        send_brevo_email(email, name, "1_Ebook_AI_Income_Blueprint.pdf")
        return {"status": "ok"}, 200
    except Exception as e:
        return {"error": str(e)}, 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
