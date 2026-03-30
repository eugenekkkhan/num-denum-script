from telethon import TelegramClient
from telethon import functions
from telethon.errors import ChatNotModifiedError
from telethon.tl.types import Channel, Chat
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pynput import keyboard

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
DENOMINATOR_TAG = "[Z]"

custom_data = {
    "SEMESTER_START": SEMESTER_START,
    "NUMERATOR_TAG": NUMERATOR_TAG,
    "DENOMINATOR_TAG": DENOMINATOR_TAG,
    "CHECK_INTERVAL": CHECK_INTERVAL,
    "CHAT_IDS": CHAT_IDS,
}

handle_change_data = lambda key, value: custom_data.update({key: value})

def interface():
    what_to_change = ""
    while what_to_change != "-1":
        what_to_change = input("What do you want to change? (SEMESTER_START, NUMERATOR_TAG, DENOMINATOR_TAG, CHECK_INTERVAL, CHAT_IDS, -1 - cancel): ")
        if what_to_change == "-1":
            break
        if what_to_change not in custom_data:
            print("Invalid option. Please try again.")
            return
        new_value = input(f"Enter new value for {what_to_change}: ")
        handle_change_data(what_to_change, new_value)
        print(f"{what_to_change} updated successfully!")

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
        current_title = getattr(entity, "title", None)

        if not current_title:
            print(f"Skipping {chat_id}: entity does not have a title.")
            continue

        if current_tag not in current_title:
            new_title = switch_title(current_title)
            if new_title == current_title:
                print(f"Skipping {chat_id}: title has no semester tag to swap.")
                continue

            if isinstance(entity, Channel):
                try:
                    await client(functions.channels.EditTitleRequest(
                        channel=entity,
                        title=new_title
                    ))
                except ChatNotModifiedError:
                    print(f"Skipping {chat_id}: title is already up to date.")
            elif isinstance(entity, Chat):
                try:
                    await client(functions.messages.EditChatTitleRequest(
                        chat_id=entity.id,
                        title=new_title
                    ))
                except ChatNotModifiedError:
                    print(f"Skipping {chat_id}: title is already up to date.")
            else:
                print(f"Skipping {chat_id}: unsupported entity type {type(entity).__name__}.")

async def main() -> None:
    client = TelegramClient("session_name", API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    print("Client started successfully!")
    # dialogs = await client.get_dialogs()
    # print("Available chats:")
    # for dialog in dialogs:
    #     if isinstance(dialog.entity, Channel):
    #         print(f"{dialog.id}: {dialog.name}")

    state_of_interface = ""
    with keyboard.Events() as events:
        while True:
            await update_chats(client)
            seconds_to_sleep = CHECK_INTERVAL - int(time_spent_in_current_week().total_seconds())
            await custom_sleep(seconds_to_sleep)


if __name__ == "__main__":
    asyncio.run(main())