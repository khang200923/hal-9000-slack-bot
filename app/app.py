import os
import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import llm
import time
import threading
import schedule
import pytz

load_dotenv()
pytz.timezone('Asia/Bangkok')
app = App()
joined_users = []

@app.event("member_joined_channel")
def handle_team_join(event, say):
    if event["channel"] != os.environ.get("THE_CHANNEL_ID"):
        return
    user_id = event["user"]
    if user_id in joined_users:
        return
    joined_users.append(user_id)
    user_info = app.client.users_info(user=user_id)
    welcome = llm.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[llm.systemp(llm.get("prompts/welcome.md").format(info=user_info.data["user"], datetime=datetime.datetime.now().isoformat()))],
        max_tokens=300
    ).choices[0].message.content
    say(welcome)

def midnight():
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

def schedule_midnight():
    def job():
        midnight()

    schedule.every().day.at("00:00").do(job)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

def schedules():
    # schedule_midnight()
    pass

def main():
    schedules()
    handler = SocketModeHandler(app, app_token=os.environ.get("SLACK_APP_TOKEN"))
    handler.start()

if __name__ == "__main__":
    main()
