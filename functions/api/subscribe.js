export async function onRequestPost(context) {
  try {
    const formData = await context.request.formData();
    const email = formData.get('email')?.trim();
    const name = formData.get('name')?.trim() || '';
    const token = formData.get('cf-turnstile-response');

    // Validar email
    if (!email || !email.includes('@')) {
      return new Response(JSON.stringify({ error: 'Email inválido' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Validar Turnstile (bot protection)
    const turnstileValidation = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        secret: context.env.TURNSTILE_SECRET_KEY,
        response: token
      })
    });

    const turnstileResult = await turnstileValidation.json();
    if (!turnstileResult.success) {
      return new Response(JSON.stringify({ error: 'Validação falhou. Tente novamente.' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Chamar Brevo API
    const brevoHeaders = {
      'api-key': context.env.BREVO_API_KEY,
      'Content-Type': 'application/json'
    };

    const payload = {
      email: email,
      listIds: [2], // Lista 2
      attributes: {}
    };

    if (name) {
      const nameParts = name.split(' ');
      payload.attributes.FIRSTNAME = nameParts[0];
      payload.attributes.LASTNAME = nameParts.slice(1).join(' ');
    }

    const brevoResponse = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: brevoHeaders,
      body: JSON.stringify(payload)
    });

    if (brevoResponse.status === 201 || brevoResponse.status === 204) {
      return new Response(JSON.stringify({
        success: true,
        message: 'Inscrito! Verifique seu email em 5 minutos.'
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } else if (brevoResponse.status === 400) {
      return new Response(JSON.stringify({
        success: true,
        message: 'Email já estava cadastrado'
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } else {
      return new Response(JSON.stringify({ error: 'Erro ao inscrever. Tente novamente.' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

  } catch (error) {
    return new Response(JSON.stringify({ error: `Erro: ${error.message}` }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
