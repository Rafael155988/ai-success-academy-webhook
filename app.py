#!/usr/bin/env python3
"""
AI Success Academy - Stripe Webhook Handler com Brevo Integration
Author: Claude AI
Versão: 2.0 (Production Ready)
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
# SETUP LOGGING - Essencial para debug no Render
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Render captura stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================================================
# CARREGAR CREDENCIAIS DO AMBIENTE
# ============================================================================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

logger.info("=== INICIALIZANDO APP ===")
logger.info(f"STRIPE_SECRET_KEY: {'✅ Carregada' if STRIPE_SECRET_KEY else '❌ FALTANDO'}")
logger.info(f"STRIPE_WEBHOOK_SECRET: {'✅ Carregada' if STRIPE_WEBHOOK_SECRET else '❌ FALTANDO'}")
logger.info(f"BREVO_API_KEY: {'✅ Carregada' if BREVO_API_KEY else '❌ FALTANDO'}")

# Validar credenciais
if not all([STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, BREVO_API_KEY]):
    logger.error("❌ CREDENCIAIS FALTANDO! Verifique as environment variables no Render Dashboard")
    logger.error("Variáveis necessárias:")
    logger.error("  - STRIPE_SECRET_KEY")
    logger.error("  - STRIPE_WEBHOOK_SECRET")
    logger.error("  - BREVO_API_KEY")

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

# URLs dos PDFs no Cloudflare R2 (ATUALIZE COM URLS REAIS)
PDF_URLS = {
    "1_Ebook_AI_Income_Blueprint.pdf": "https://r2-ai-success.s3.amazonaws.com/1_Ebook_AI_Income_Blueprint.pdf",
    "2_Bonus_7_Essential_AI_Tools.pdf": "https://r2-ai-success.s3.amazonaws.com/2_Bonus_7_Essential_AI_Tools.pdf",
    "3_Bonus_AI_Business_Launch_Workbook.pdf": "https://r2-ai-success.s3.amazonaws.com/3_Bonus_AI_Business_Launch_Workbook.pdf",
    "4_Order_Bump_200_AI_Prompts.pdf": "https://r2-ai-success.s3.amazonaws.com/4_Order_Bump_200_AI_Prompts.pdf"
}

logger.info(f"Mapeamento de preços carregado: {len(PRICE_TO_PDF_MAPPING)} produtos")

# ============================================================================
# FUNÇÕES DE INTEGRAÇÃO
# ============================================================================

def create_brevo_contact(email, name=None):
    """
    Criar ou atualizar contato no Brevo
    
    Args:
        email (str): Email do cliente
        name (str): Nome do cliente
        
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        logger.info(f"→ Criando contato no Brevo: {email}")
        
        url = "https://api.brevo.com/v3/contacts"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        payload = {
            "email": email,
            "attributes": {"FIRSTNAME": name or "Customer"},
            "listIds": [2]  # Lista padrão
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [201, 204]:
            logger.info(f"✅ Contato criado/atualizado: {email}")
            return True
        else:
            logger.error(f"❌ Erro Brevo (status {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exceção ao criar contato: {str(e)}")
        return False


def send_brevo_email(email, name, pdf_filename):
    """
    Enviar email transacional com link do PDF
    
    Args:
        email (str): Email do destinatário
        name (str): Nome do destinatário
        pdf_filename (str): Nome do arquivo PDF
        
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        logger.info(f"→ Enviando email para: {email} (PDF: {pdf_filename})")
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        pdf_url = PDF_URLS.get(pdf_filename, "")
        
        if not pdf_url:
            logger.warning(f"⚠️ URL do PDF não encontrada para: {pdf_filename}")
        
        payload = {
            "to": [{"email": email, "name": name or "Customer"}],
            "subject": "Seu Bônus Exclusivo - AI Success Academy 🚀",
            "htmlContent": f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Obrigado pela compra!</h2>
                    <p>Aqui está seu bônus exclusivo:</p>
                    <p><a href="{pdf_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        📥 Baixar seu PDF
                    </a></p>
                    <p>Aproveite e comece sua jornada com AI Success Academy!</p>
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
            logger.error(f"❌ Erro ao enviar email (status {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exceção ao enviar email: {str(e)}")
        return False


# ============================================================================
# ROTAS DA APLICAÇÃO
# ============================================================================

@app.route("/health", methods=["GET"])
def health():
    """Verificar saúde da aplicação"""
    logger.info("GET /health")
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
    """
    Processar webhooks do Stripe
    
    Eventos processados:
    - charge.succeeded: Quando um pagamento é bem-sucedido
    """
    
    logger.info("=" * 60)
    logger.info("WEBHOOK STRIPE RECEBIDO")
    logger.info("=" * 60)
    
    try:
        # 1. VALIDAR ASSINATURA
        sig_header = request.headers.get("Stripe-Signature")
        logger.info(f"Stripe-Signature header: {'Presente' if sig_header else 'AUSENTE'}")
        
        if not sig_header:
            logger.error("❌ Header Stripe-Signature não encontrado")
            return {"error": "No Stripe-Signature header"}, 400
        
        # 2. CONSTRUIR EVENTO
        try:
            event = stripe.Webhook.construct_event(
                request.get_data(),  # RAW body (não parsed JSON)
                sig_header,
                STRIPE_WEBHOOK_SECRET
            )
            logger.info(f"✅ Assinatura validada com sucesso")
        except ValueError:
            logger.error("❌ Payload JSON inválido")
            return {"error": "Invalid payload"}, 400
        except stripe.error.SignatureVerificationError:
            logger.error("❌ Assinatura inválida - webhook secret pode estar errado")
            return {"error": "Invalid signature"}, 400
        
        # 3. PROCESSAR EVENTO
        event_type = event.get("type")
        logger.info(f"Tipo de evento: {event_type}")
        
        if event_type == "charge.succeeded":
            charge = event["data"]["object"]
            
            # Extrair dados
            email = charge.get("receipt_email") or charge.get("billing_details", {}).get("email")
            name = charge.get("billing_details", {}).get("name", "Customer")
            amount = charge.get("amount", 0)
            charge_id = charge.get("id")
            
            logger.info(f"📧 Email: {email}")
            logger.info(f"👤 Name: {name}")
            logger.info(f"💰 Amount: {amount} (centavos)")
            logger.info(f"🔑 Charge ID: {charge_id}")
            
            # Validar email
            if not email:
                logger.error("❌ Email não encontrado no webhook")
                return {"status": "received", "warning": "no email"}, 200
            
            # Converter para centavos se necessário
            price_key = amount
            logger.info(f"Procurando preço: {price_key}")
            
            # 4. CRIAR CONTATO NO BREVO
            contact_success = create_brevo_contact(email, name)
            
            # 5. ENVIAR EMAIL COM PDF
            pdf_filename = PRICE_TO_PDF_MAPPING.get(price_key)
            
            if pdf_filename:
                logger.info(f"PDF encontrado: {pdf_filename}")
                email_success = send_brevo_email(email, name, pdf_filename)
                logger.info(f"Email enviado: {'✅' if email_success else '❌'}")
            else:
                logger.warning(f"⚠️ Preço {price_key} não mapeado para nenhum PDF")
                logger.info(f"Preços conhecidos: {list(PRICE_TO_PDF_MAPPING.keys())}")
            
            logger.info("=" * 60)
            logger.info("✅ WEBHOOK PROCESSADO COM SUCESSO")
            logger.info("=" * 60)
            
        else:
            logger.info(f"Evento {event_type} ignorado (não processamos este tipo)")
        
        return {"status": "received", "event_type": event_type}, 200
        
    except Exception as e:
        logger.error(f"❌ ERRO NÃO CAPTURADO: {str(e)}")
        logger.error(f"Traceback: {e.__class__.__name__}")
        return {"error": str(e)}, 500


@app.route("/api/price-to-pdf-mapping", methods=["GET"])
def get_mapping():
    """Retornar mapeamento de preços"""
    logger.info("GET /api/price-to-pdf-mapping")
    return {"mapping": PRICE_TO_PDF_MAPPING}, 200


@app.route("/api/test-brevo", methods=["POST"])
def test_brevo():
    """
    Testar integração com Brevo
    
    POST body: {"email": "test@example.com", "name": "Test"}
    """
    try:
        logger.info("POST /api/test-brevo")
        data = request.get_json() or {}
        email = data.get("email")
        name = data.get("name", "Test")
        
        if not email:
            return {"error": "Email required"}, 400
        
        logger.info(f"Testando Brevo com: {email}")
        
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
# INICIAR APLICAÇÃO
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🚀 Iniciando Flask em 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
