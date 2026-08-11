# ---- Bot behaviour settings ----

# How often (in seconds) the bot checks for new unread messages
POLL_INTERVAL_SECONDS = 5

# Max number of unread chats to process in a single check cycle
MAX_UNREAD_CHATS_PER_CYCLE = 5

# How many back-and-forth turns to remember per contact (keeps replies relevant
# without sending your whole chat history to the API every time)
MAX_HISTORY_TURNS = 10

# Folder where your WhatsApp Web login session is stored, so you don't have to
# scan the QR code every single time you run the bot
CHROME_PROFILE_DIR = "./whatsapp_profile"

# Gemini model to use. gemini-1.5-flash = fast + generous free tier.
MODEL_NAME = "gemini-3.5-flash"

# Names of contacts/groups the bot should NEVER auto-reply to.
# Match this to exactly how the name/title appears in WhatsApp.
IGNORE_LIST = [
    # "Mom",
    # "College Group",
]

# The "personality" of your auto-reply bot. Edit this freely.
PERSONA_PROMPT = """
You are an auto-reply assistant for WhatsApp, replying on behalf of the user while
they're away.

Every reply MUST start with exactly this line, on its own:
"HEY This is an automated message. The user will get to you shortly!"

After that line, add a short (1-2 sentence), friendly, relevant response to what
the person said or asked. Keep it casual and natural. Do not promise specific
information or make commitments on the user's behalf - just acknowledge their
message so they know it's been seen.
"""