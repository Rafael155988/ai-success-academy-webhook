
# ============================================================================
# ROTA PARA CRIAR SESSÃO DE CHECKOUT
# ============================================================================

@app.route("/api/create-checkout", methods=["POST"])
def create_checkout():
    """Criar sessão de checkout do Stripe"""
    try:
        data = request.get_json() or {}
        amount = data.get("amount")
        
        if not amount:
            return {"error": "Amount required"}, 400
        
        logger.info(f"Criando checkout para: ${amount/100:.2f}")
        
        # Criar sessão de checkout
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount,
                        "product_data": {
                            "name": "AI Income Blueprint Bundle",
                            "description": "Complete AI business package",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="https://divine-waterfall-50d5.rafaeloliveiragomes0.workers.dev/thankyou.html",
            cancel_url="https://divine-waterfall-50d5.rafaeloliveiragomes0.workers.dev/index.html",
        )
        
        logger.info(f"✅ Sessão criada: {session.id}")
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }, 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar checkout: {str(e)}")
        return {"error": str(e)}, 500
