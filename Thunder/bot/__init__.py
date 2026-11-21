"""The primary Pyrogram client and the shared workload tables."""

from pyrogram import Client
from Thunder.vars import Var

StreamBot = Client(
    # Fresh session name: the old "Web Streamer.session" was created by
    # pyrofork and wzgram cannot open it (table update_state already
    # exists). A new name forces a clean login with BOT_TOKEN.
    name="Web Streamer2",
    api_id=Var.API_ID,
    api_hash=Var.API_HASH,
    bot_token=Var.BOT_TOKEN,
    sleep_threshold=Var.SLEEP_THRESHOLD,
    workers=Var.WORKERS,
    max_concurrent_transmissions=1000,
)

multi_clients = {}
work_loads = {}
