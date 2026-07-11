import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { Resend } from "https://esm.sh/resend@2.0.0"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('Received request')
    const { name, sender_email, message_text, recipient } = await req.json()
    console.log('Request data:', { name, sender_email, recipient })

    if (!name || !sender_email || !message_text || !recipient) {
      console.error('Missing required fields')
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Check for Resend API key
    const resendApiKey = Deno.env.get('RESEND_API_KEY')
    console.log('Resend API key present:', !!resendApiKey)
    
    if (!resendApiKey) {
      console.error('RESEND_API_KEY not set in environment')
      return new Response(
        JSON.stringify({ error: 'RESEND_API_KEY not configured' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Initialize Resend with API key from environment
    const resend = new Resend(resendApiKey)

    console.log('Sending email via Resend...')
    // Send email using Resend
    const data = await resend.emails.send({
      from: 'onboarding@resend.dev',
      to: recipient,
      subject: `Portfolio contact from ${name}`,
      html: `
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> ${name}</p>
        <p><strong>Email:</strong> ${sender_email}</p>
        <p><strong>Message:</strong></p>
        <p>${message_text}</p>
      `,
      text: `Name: ${name}\nEmail: ${sender_email}\n\nMessage:\n${message_text}`,
    })
    console.log('Resend response:', data)

    // Log email to Supabase Storage
    const timestamp = new Date().toISOString()
    const logEntry = {
      timestamp,
      name,
      sender_email,
      recipient,
      message_text,
      status: 'sent',
      resend_id: data.id,
    }

    console.log('Email log:', JSON.stringify(logEntry))

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Email sent successfully',
        data 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error sending email:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Failed to send email',
        details: error.message,
        stack: error.stack 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
