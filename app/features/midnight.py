import os
import threading
import time
from dotenv import load_dotenv
import schedule
import llm
from slack_bolt import App

load_dotenv('..')

def midnight(app: App):
    # Summon everyone to tell me to go to bed and sleep and stop slacking
    channel_id = os.environ.get("THE_CHANNEL_ID")
    creator_id = os.environ.get("THE_CREATOR_ID")
    content = llm.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[llm.systemp(llm.get("prompts/go-to-bed.md").format(creator=creator_id, pronouns=os.environ.get("PRONOUNS")))],
        max_tokens=200,
        temperature=0.7
    ).choices[0].message.content
    app.client.chat_postMessage(channel=channel_id, text=content)

def schedule_midnight(app: App):
    def job():
        midnight(app)

    schedule.every().day.at("00:00").do(job)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

def feature(app: App):
    schedule_midnight(app)

    print("Midnight feature enabled.")
