# WhatsApp AI Auto-Reply Bot (Gemini API)

Auto-replies to your WhatsApp messages using Google's Gemini API (free tier) —
no OpenAI, no paid API required.

## How it works

- Selenium opens WhatsApp Web in Chrome and logs in via QR scan (once).
- Every few seconds, it checks for unread chats.
- For each unread message, it sends the text to Gemini and gets a reply.
- It types and sends that reply back in the chat, just like a human would.
- Each contact gets their own conversation memory, so replies stay contextual.

## Setup

1. **Get a free Gemini API key**
   Go to https://aistudio.google.com/apikey and create a key. No credit card needed.

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   (Chrome must be installed on your machine — Selenium will auto-download
   the matching ChromeDriver via `webdriver-manager`.)

3. **Add your API key**
   Copy `.env.example` to `.env` and paste your key in:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```
   Never commit `.env` to GitHub — it's already in `.gitignore`.

4. **Run the bot**
   ```bash
   python whatsapp_bot.py
   ```
   A Chrome window opens with a QR code. Scan it from your phone:
   WhatsApp → Settings → Linked Devices → Link a Device.

   After the first login, your session is saved in `whatsapp_profile/`, so
   you won't need to scan again on future runs (as long as you don't delete
   that folder or log out from your phone).

5. **Customize the bot's personality**
   Edit `PERSONA_PROMPT` in `config.py` to change tone, add context about
   yourself, or set reply rules.

6. **Stop the bot**
   Press `Ctrl+C` in the terminal.

## Files

| File | Purpose |
|---|---|
| `whatsapp_bot.py` | Main script — Selenium automation loop |
| `gemini_client.py` | Talks to Gemini API, keeps per-contact chat history |
| `config.py` | All settings: poll interval, persona, ignore list, model |
| `.env` | Your API key (you create this, never commit it) |
| `replied_messages.json` | Auto-generated log to avoid double-replying |

## Important notes

- **This is not an official WhatsApp Business API integration.** It automates
  your personal WhatsApp account through WhatsApp Web, which is against
  WhatsApp's Terms of Service. It's fine for a personal side project, but
  there's a real (if fairly small) risk of a temporary block if you message
  too fast or too often — the delays in the code are there to reduce that
  risk, don't remove them.
- **Selectors may break.** WhatsApp updates its web app's HTML structure
  periodically. If the bot stops detecting chats or messages, the XPath
  selectors in `whatsapp_bot.py` (in `get_unread_chats`,
  `get_last_incoming_message`, `send_reply`) are the first thing to check —
  right-click the relevant element in WhatsApp Web and "Inspect" to find the
  new selector.
- **Add people you don't want auto-replied to** (e.g. close friends, family,
  work groups) to `IGNORE_LIST` in `config.py` — you don't want the AI
  replying to your mom without you knowing.
- **Free tier limits**: Gemini's free tier is generous but not unlimited
  (roughly 15 requests/min at time of writing). Check current limits at
  https://ai.google.dev/pricing if the bot starts erroring out.
