import os
from flask import Flask, request, jsonify, Response
import requests
from datetime import datetime

app = Flask(__name__)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
LISTA_2_ID = 2

LEAD_MAGNET_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt Starter Pack Grátis - AI Success Academy</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --navy: #0B1B2E; --navy-soft: #122742; --gold: #D4AF37; --gold-bright: #F0CD63; --paper: #F5F1E8; --body-on-dark: #C9D2DE; --muted: #8492A6; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, var(--navy) 0%, var(--navy-soft) 100%); color: var(--body-on-dark); min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }
        .nav { position: fixed; top: 0; width: 100%; background: rgba(11, 27, 46, 0.92); backdrop-filter: blur(6px); border-bottom: 1px solid #23405F; z-index: 50; padding: 16px 24px; }
        .nav-content { max-width: 1120px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
        .brand { font-family: 'Fraunces', serif; font-weight: 700; color: #FAF7EF; font-size: 18px; }
        .brand span { color: var(--gold); }
        .nav-links { display: flex; gap: 24px; list-style: none; }
        .nav-links a { color: var(--body-on-dark); text-decoration: none; font-size: 14px; transition: color 0.2s; }
        .nav-links a:hover { color: var(--gold); }
        .container { background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%; padding: 48px 40px; margin-top: 80px; margin-bottom: 40px; }
        .badge { display: inline-block; background: var(--gold); color: var(--navy); padding: 8px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 20px; letter-spacing: 0.5px; }
        h1 { font-family: 'Fraunces', serif; color: var(--navy); font-size: 36px; margin-bottom: 12px; line-height: 1.1; font-weight: 700; }
        .subtitle { color: #666; font-size: 16px; margin-bottom: 32px; line-height: 1.6; }
        .benefits { background: var(--paper); border-left: 4px solid var(--gold); padding: 20px; border-radius: 8px; margin-bottom: 32px; font-size: 14px; color: var(--navy); }
        .benefits strong { display: block; color: var(--navy); margin-bottom: 12px; font-weight: 600; }
        .benefits ul { list-style: none; margin: 0; }
        .benefits li { padding-left: 24px; position: relative; margin-bottom: 8px; line-height: 1.5; }
        .benefits li:before { content: "✓"; position: absolute; left: 0; color: var(--gold); font-weight: bold; font-size: 16px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 14px; font-weight: 600; color: var(--navy); margin-bottom: 8px; }
        input { width: 100%; padding: 14px 16px; border: 1px solid #E2DBC8; border-radius: 8px; font-size: 16px; font-family: inherit; transition: all 0.2s; color: var(--navy); }
        input::placeholder { color: var(--muted); }
        input:focus { outline: none; border-color: var(--gold); box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.1); }
        button { width: 100%; padding: 16px 20px; background: var(--gold); color: var(--navy); border: none; border-radius: 8px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.3s; margin-top: 8px; }
        button:hover:not(:disabled) { background: var(--gold-bright); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(212, 175, 55, 0.3); }
        button:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .message { margin-top: 16px; padding: 14px 16px; border-radius: 8px; font-size: 14px; display: none; border: 1px solid; }
        .message.success { background: #d4edda; color: #155724; border-color: #c3e6cb; display: block; }
        .message.error { background: #f8d7da; color: #721c24; border-color: #f5c6cb; display: block; }
        .footer { color: var(--muted); font-size: 13px; margin-top: 20px; text-align: center; }
        .footer a { color: var(--gold); text-decoration: none; }
        .footer a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-content">
            <div class="brand">AI Success <span>Academy</span></div>
            <ul class="nav-links">
                <li><a href="https://blog.theaisuccessacademy.com/">Blog</a></li>
                <li><a href="https://theaisuccessacademy.com/">Produtos</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <div class="badge">🎁 Lead Magnet Gratuito</div>
        <h1>Receba seu Prompt Starter Pack</h1>
        <p class="subtitle">10 prompts profissionais prontos para usar. Enviaremos por email em menos de 5 minutos.</p>
        
        <div class="benefits">
            <strong>O que você vai receber:</strong>
            <ul>
                <li>10 prompts testados e validados</li>
                <li>Prontos para usar em ChatGPT, Claude e outras IAs</li>
                <li>PDF editável para sua biblioteca pessoal</li>
                <li>+ 5 emails com dicas e estratégias exclusivas</li>
            </ul>
        </div>
        
        <form id="subscribeForm">
            <div class="form-group">
                <label for="name">Seu nome (opcional)</label>
                <input type="text" id="name" name="name" placeholder="Rafael">
            </div>
            
            <div class="form-group">
                <label for="email">Seu melhor email *</label>
                <input type="email" id="email" name="email" placeholder="seu@email.com" required>
            </div>
            
            <button type="submit" id="submitBtn">Receber Prompt Pack Grátis</button>
            <div class="message" id="message"></div>
            
            <p class="footer">Sem spam. Você pode desinscrever-se quando quiser. <a href="https://blog.theaisuccessacademy.com/">Voltar ao blog</a></p>
        </form>
    </div>

    <script>
        const form = document.getElementById('subscribeForm');
        const submitBtn = document.getElementById('submitBtn');
        const message = document.getElementById('message');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value.trim();
            const name = document.getElementById('name').value.trim();
            
            if (!email) {
                message.textContent = '✗ Email é obrigatório';
                message.className = 'message error';
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
            message.style.display = 'none';
            
            try {
                const response = await fetch('/api/subscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, name })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    message.textContent = '✓ Sucesso! Verifique seu email em 5 minutos.';
                    message.className = 'message success';
                    form.reset();
                    submitBtn.textContent = 'Receber Prompt Pack Grátis';
                } else {
                    message.textContent = '✗ ' + (data.error || 'Erro ao inscrever. Tente novamente.');
                    message.className = 'message error';
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Receber Prompt Pack Grátis';
                }
            } catch (error) {
                message.textContent = '✗ Erro de conexão. Tente novamente.';
                message.className = 'message error';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Receber Prompt Pack Grátis';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/lead-magnet', methods=['GET'])
def lead_magnet():
    return Response(LEAD_MAGNET_HTML, mimetype='text/html; charset=utf-8')

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    try:
        data = request.json
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        
        if not email:
            return jsonify({"error": "Email é obrigatório"}), 400
        
        if '@' not in email:
            return jsonify({"error": "Email inválido"}), 400
        
        headers = {"api-key": BREVO_API_KEY, "Content-Type": "application/json"}
        payload = {"email": email, "listIds": [LISTA_2_ID]}
        
        if name:
            first_name = name.split()[0] if name else ""
            last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
            payload["attributes"] = {"FIRSTNAME": first_name, "LASTNAME": last_name}
        
        response = requests.post("https://api.brevo.com/v3/contacts", json=payload, headers=headers, timeout=10)
        
        if response.status_code in [201, 204]:
            return jsonify({"success": True, "message": "Inscrito! Verifique seu email em 5 min."}), 201
        elif response.status_code == 400:
            return jsonify({"success": True, "message": "Email já estava cadastrado"}), 200
        else:
            return jsonify({"error": f"Erro: {response.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=False)
