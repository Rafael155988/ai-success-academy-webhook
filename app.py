#!/usr/bin/env python3
"""
AI Success Academy - Stripe Webhook Handler com Brevo Integration
Versão: 3.0 (PRODUCTION - URLs Configuráveis)
"""

import os
import json
import logging
import sys
import stripe
import requests
from datetime import datetime
from flask import Flask, request

# ============================================================================
# SETUP LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================================================
# CARREGAR CREDENCIAIS
# ============================================================================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

logger.info("=== INICIALIZANDO APP ===")
logger.info(f"STRIPE_SECRET_KEY: {'✅' if STRIPE_SECRET_KEY else '❌'}")
logger.info(f"STRIPE_WEBHOOK_SECRET: {'✅' if STRIPE_WEBHOOK_SECRET else '❌'}")
logger.info(f"BREVO_API_KEY: {'✅' if BREVO_API_KEY else '❌'}")

if not all([STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, BREVO_API_KEY]):
    logger.error("❌ CREDENCIAIS FALTANDO!")

stripe.api_key = STRIPE_SECRET_KEY

# ============================================================================
# MAPEAMENTO DE PREÇOS PARA PDFs
# ============================================================================
PRICE_TO_PDF_MAPPING = {
    2700: "1_Ebook_AI_Income_Blueprint.pdf",
    4700: "2_Bonus_7_Essential_AI_Tools.pdf",
    6700: "3_Bonus_AI_Business_Launch_Workbook.pdf",
    9700: "4_Order_Bump_200_AI_Prompts.pdf"
}

# URLs DOS PDFs - ATUALIZE COM URLS REAIS DO CLOUDFLARE R2
PDF_URLS = {
    "1_Ebook_AI_Income_Blueprint.pdf": "https://pdfs.aisuccessacademy.com/1_Ebook_AI_Income_Blueprint.pdf",
    "2_Bonus_7_Essential_AI_Tools.pdf": "https://pdfs.aisuccessacademy.com/2_Bonus_7_Essential_AI_Tools.pdf",
    "3_Bonus_AI_Business_Launch_Workbook.pdf": "https://pdfs.aisuccessacademy.com/3_Bonus_AI_Business_Launch_Workbook.pdf",
    "4_Order_Bump_200_AI_Prompts.pdf": "https://pdfs.aisuccessacademy.com/4_Order_Bump_200_AI_Prompts.pdf"
}

logger.info(f"Mapeamento de preços: {len(PRICE_TO_PDF_MAPPING)} produtos")

# ============================================================================
# FUNÇÕES DE INTEGRAÇÃO
# ============================================================================

def create_brevo_contact(email, name=None):
    """Criar contato no Brevo"""
    try:
        logger.info(f"→ Criando contato: {email}")
        
        url = "https://api.brevo.com/v3/contacts"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        payload = {
            "email": email,
            "attributes": {"FIRSTNAME": name or "Customer"},
            "listIds": [2]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [201, 204]:
            logger.info(f"✅ Contato criado: {email}")
            return True
        else:
            logger.error(f"❌ Erro Brevo ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar contato: {str(e)}")
        return False


def send_brevo_email(email, name, pdf_filename):
    """Enviar email com link do PDF"""
    try:
        logger.info(f"→ Enviando email: {email} (PDF: {pdf_filename})")
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        pdf_url = PDF_URLS.get(pdf_filename, "")
        
        if not pdf_url:
            logger.warning(f"⚠️ URL não encontrada: {pdf_filename}")
        
        payload = {
            "to": [{"email": email, "name": name or "Customer"}],
            "subject": "Seu Bônus Exclusivo - AI Success Academy 🚀",
            "htmlContent": f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                        <h2 style="color: #333;">Obrigado pela compra!</h2>
                        <p style="color: #666; font-size: 16px;">Aqui está seu bônus exclusivo:</p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{pdf_url}" style="background-color: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">
                                📥 Baixar seu PDF Agora
                            </a>
                        </p>
                        <p style="color: #666; font-size: 14px;">Aproveite e comece sua jornada com AI Success Academy!</p>
                    </div>
                </body>
            </html>
            """,
            "from": {
                "email": "noreply@aisuccessacademy.com",
                "name": "AI Success Academy"
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [201, 202]:
            logger.info(f"✅ Email enviado: {email}")
            return True
        else:
            logger.error(f"❌ Erro email ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao enviar email: {str(e)}")
        return False


# ============================================================================
# ROTAS
# ============================================================================

@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "stripe_configured": bool(STRIPE_SECRET_KEY),
            "brevo_configured": bool(BREVO_API_KEY)
        }
    }, 200


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Processar webhooks do Stripe"""
    
    logger.info("=" * 60)
    logger.info("WEBHOOK STRIPE RECEBIDO")
    logger.info("=" * 60)
    
    try:
        sig_header = request.headers.get("Stripe-Signature")
        logger.info(f"Signature header: {'Presente' if sig_header else 'AUSENTE'}")
        
        if not sig_header:
            return {"error": "No Stripe-Signature header"}, 400
        
        try:
            event = stripe.Webhook.construct_event(
                request.get_data(),
                sig_header,
                STRIPE_WEBHOOK_SECRET
            )
            logger.info(f"✅ Assinatura validada")
        except ValueError:
            return {"error": "Invalid payload"}, 400
        except stripe.error.SignatureVerificationError:
            logger.error("❌ Assinatura inválida")
            return {"error": "Invalid signature"}, 400
        
        event_type = event.get("type")
        logger.info(f"Evento: {event_type}")
        
        if event_type == "charge.succeeded":
            charge = event["data"]["object"]
            email = charge.get("receipt_email") or charge.get("billing_details", {}).get("email")
            name = charge.get("billing_details", {}).get("name", "Customer")
            amount = charge.get("amount", 0)
            charge_id = charge.get("id")
            
            logger.info(f"📧 Email: {email}")
            logger.info(f"👤 Name: {name}")
            logger.info(f"💰 Amount: ${amount/100:.2f}")
            logger.info(f"🔑 Charge ID: {charge_id}")
            
            if not email:
                logger.error("❌ Email não encontrado")
                return {"status": "received", "warning": "no email"}, 200
            
            # Criar contato
            create_brevo_contact(email, name)
            
            # Enviar email com PDF
            pdf_filename = PRICE_TO_PDF_MAPPING.get(amount)
            
            if pdf_filename:
                logger.info(f"PDF: {pdf_filename}")
                send_brevo_email(email, name, pdf_filename)
            else:
                logger.warning(f"⚠️ Preço {amount} não mapeado")
            
            logger.info("✅ WEBHOOK PROCESSADO COM SUCESSO")
            
        return {"status": "received", "event_type": event_type}, 200
        
    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}")
        return {"error": str(e)}, 500


@app.route("/api/price-to-pdf-mapping", methods=["GET"])
def get_mapping():
    """Retornar mapeamento de preços"""
    return {"mapping": PRICE_TO_PDF_MAPPING}, 200


@app.route("/api/test-brevo", methods=["POST"])
def test_brevo():
    """Testar integração com Brevo"""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        name = data.get("name", "Test")
        
        if not email:
            return {"error": "Email required"}, 400
        
        create_brevo_contact(email, name)
        send_brevo_email(email, name, "1_Ebook_AI_Income_Blueprint.pdf")
        
        return {"status": "test_sent", "email": email}, 200
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {str(e)}")
        return {"error": str(e)}, 400


@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas"""
    logger.warning(f"404 - Rota não encontrada: {request.path}")
    return {"error": "Not found", "path": request.path}, 404


# ============================================================================
# INICIAR APP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🚀 Iniciando em 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
