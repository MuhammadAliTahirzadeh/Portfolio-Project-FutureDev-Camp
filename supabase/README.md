# Supabase Email Integration

This directory contains the Supabase Edge Function for sending emails via Resend.

## Setup Instructions

### 1. Get Resend API Key
- Sign up at https://resend.com
- Get your API key from the dashboard
- Add it to your Supabase project environment variables

### 2. Deploy Edge Function
Install Supabase CLI if not already installed:
```bash
npm install -g supabase
```

Link your Supabase project:
```bash
supabase link --project-ref skducwmikaszbjphorqk
```

Set the Resend API key in Supabase:
```bash
supabase secrets set RESEND_API_KEY=your_resend_api_key_here
```

Deploy the Edge Function:
```bash
supabase functions deploy send-email
```

### 3. Set Up Storage Bucket (Optional)
For email logging, create a storage bucket in your Supabase dashboard:
1. Go to Storage > Create a new bucket
2. Name it `email-logs`
3. Configure appropriate RLS policies

### 4. Update Local .env
Add your Resend API key to your local `.env` file:
```
RESEND_API_KEY=your_actual_resend_api_key
```

## Testing
Test the Edge Function locally:
```bash
supabase functions serve send-email
```

Or test via curl:
```bash
curl -X POST 'https://skducwmikaszbjphorqk.supabase.co/functions/v1/send-email' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test User",
    "sender_email": "test@example.com",
    "message_text": "This is a test message",
    "recipient": "muhammadali.tahirzadeh.uni@gmail.com"
  }'
```

## Notes
- The Edge Function uses Resend for email delivery
- Email recipient is set to muhammadali.tahirzadeh.uni@gmail.com
- SQLite database remains unchanged for messages/projects
- Email logs are currently logged to console; storage integration can be added later
