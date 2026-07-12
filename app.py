#!/usr/bin/env python3
"""AI Success Academy - Stripe Webhook Handler (FIXED)"""
import os, json, sys, stripe, requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

if not all([STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, BREVO_API_KEY]):
    print("ERROR: Missing environment variables"); sys.exit(1)

stripe.api_key = STRIPE_SECRET_KEY
BREVO_API_URL = "https://api.brevo.com/v3"
BREVO_HEADERS = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}

PRICE_TO_PDF_MAPPING = {2700: "1_Ebook_AI_Income_Blueprint.pdf", 4700: "2_Bonus_7_Essential_AI_Tools.pdf", 6700: "3_Bonus_AI_Business_Launch_Workbook.pdf", 9700: "4_Order_Bump_200_AI_Prompts.pdf"}

PDF_URLS = {"1_Ebook_AI_Income_Blueprint.pdf": "https://ai-success-academy.r2.io/1_Ebook_AI_Income_Blueprint.pdf", "2_Bonus_7_Essential_AI_Tools.pdf": "https://ai-success-academy.r2.io/2_Bonus_7_Essential_AI_Tools.pdf", "3_Bonus_AI_Business_Launch_Workbook.pdf": "https://ai-success-academy.r2.io/3_Bonus_AI_Business_Launch_Workbook.pdf", "4_Order_Bump_200_AI_Prompts.pdf": "https://ai-success-academy.r2.io/4_Order_Bump_200_AI_Prompts.pdf", "5_Upsell_AI_Business_Starter_Kit.pdf": "https://ai-success-academy.r2.io/5_Upsell_AI_Business_Starter_Kit.pdf", "6_Downsell_Income_Blueprint_Quick_Start.pdf": "https://ai-success-academy.r2.io/6_Downsell_Income_Blueprint_Quick_Start.pdf"}

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        event = stripe.Webhook.construct_event(request.get_data(), request.headers.get("Stripe-Signature"), STRIPE_WEBHOOK_SECRET)
    except: return {"status": "invalid"}, 400
    
    if event["type"] == "charge.succeeded":
        charge = event["data"]["object"]
        email = charge.get("billing_details", {}).get("email") or charge.get("receipt_email")
        name = charge.get("billing_details", {}).get("name")
        amount = charge.get("amount", 0)
        
        if email:
            try:
                requests.post(f"{BREVO_API_URL}/contacts", json={"email": email, "attributes": {"FIRSTNAME": name.split()[0] if name else "Customer"}}, headers=BREVO_HEADERS, timeout=10)
                pdf_file = PRICE_TO_PDF_MAPPING.get(amount) or list(PDF_URLS.keys())[0]
                pdf_url = PDF_URLS[pdf_file]
                requests.post(f"{BREVO_API_URL}/smtp/email", json={"to": [{"email": email, "name": name or "Customer"}], "sender": {"name": "AI Success Academy", "email": "noreply@theaisuccessacademy.com"}, "subject": "Your Access Confirmed", "htmlContent": f"<h2>Welcome!</h2><p>Thank you!</p><p><a href=\"{pdf_url}\" style=\"background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;\">Download PDF</a></p>"}, headers=BREVO_HEADERS, timeout=10)
            except Exception as e: print(f"Error: {e}")
    
    return {"status": "received"}, 200

@app.route("/health", methods=["GET"])
def health(): return {"status": "ok"}, 200

@app.route("/api/stripe-status", methods=["GET"])
def stripe_status():
    try:
        stripe.Product.list(limit=1)
        return {"status": "connected"}, 200
    except: return {"status": "error"}, 500

@app.route("/api/price-to-pdf-mapping", methods=["GET"])
def mapping(): return {f"${c/100:.2f}": p for c, p in PRICE_TO_PDF_MAPPING.items()}, 200

if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))