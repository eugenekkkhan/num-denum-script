from telethon import TelegramClient
from telethon import functions
from telethon.tl.types import Channel
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")

CHAT_IDS = [
    int(c.strip()) for c in os.getenv("CHAT_IDS", "").split(",") if c.strip()
]

SEMESTER_START = os.getenv("SEMESTER_START", "2025-09-01")

CHECK_INTERVAL = 24*3600*7

NUMERATOR_TAG = "[Ч]"
DENOMINATOR_TAG = "[З]"

async def custom_sleep(seconds: int) -> None:
    for i in range(seconds):
        print(f"Sleeping for {seconds - i} seconds...", end="\r")
        await asyncio.sleep(1)

def get_current_week_number() -> int:
    start = datetime.strptime(SEMESTER_START, "%Y-%m-%d")
    today = datetime.now()
    return (today - start).days // 7

def time_spent_in_current_week() -> timedelta:
    beginning_of_week = timedelta(days=datetime.now().weekday()+1) + timedelta(hours=datetime.now().hour, minutes=datetime.now().minute, seconds=datetime.now().second)
    return beginning_of_week

def get_current_tag() -> str:
    START_SEMESTER_TAG = os.getenv("START_SEMESTER_TAG", NUMERATOR_TAG)
    week_number = get_current_week_number()

    return NUMERATOR_TAG \
        if START_SEMESTER_TAG == NUMERATOR_TAG and week_number % 2 == 0 \
        or START_SEMESTER_TAG == DENOMINATOR_TAG and week_number % 2 != 0 \
        else DENOMINATOR_TAG


def switch_title(title: str) -> str:
    return title.replace(NUMERATOR_TAG, DENOMINATOR_TAG) \
    if NUMERATOR_TAG in title \
    else title.replace(DENOMINATOR_TAG, NUMERATOR_TAG) \
    if DENOMINATOR_TAG in title else title

async def update_chats(client: TelegramClient) -> None:
    current_tag = get_current_tag()

    for chat_id in CHAT_IDS:
        entity = await client.get_entity(chat_id)
        current_title = entity.title

        if current_tag not in current_title:
            new_title = switch_title(current_title)
            await client(functions.messages.EditChatTitleRequest(
                chat_id=chat_id,
                title=new_title
            ))

async def main() -> None:
    client = TelegramClient("session_name", API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    print("Client started successfully!")

    while True:
        await update_chats(client)
        seconds_to_sleep = CHECK_INTERVAL - int(time_spent_in_current_week().total_seconds())
        await custom_sleep(seconds_to_sleep)


if __name__ == "__main__":
    asyncio.run(main())