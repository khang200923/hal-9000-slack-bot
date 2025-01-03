import datetime
import os
from dotenv import load_dotenv
from slack_bolt import App
import llm

load_dotenv('..')

def team_join(app: App):
    # @app.event("member_joined_channel")
    def handle_team_join(event, say):
        if event["channel"] != os.environ.get("THE_CHANNEL_ID"):
            return
        user_id = event["user"]
        user_info = app.client.users_info(user=user_id)
        welcome = llm.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[llm.systemp(llm.get("prompts/welcome.md").format(info=user_info.data["user"], datetime=datetime.datetime.now().isoformat()))],
            max_tokens=300
        ).choices[0].message.content
        say(welcome)
    return handle_team_join

def feature(app: App):
    app.event("member_joined_channel")(team_join(app))

    app.logger.info("Welcome feature enabled.")
