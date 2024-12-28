import os
import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import llm

load_dotenv()

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

# # debug feature
# @app.message("hahahahaha test")
# def handle_test_command(event, say):
#     if event["channel"] != os.environ.get("THE_CHANNEL_ID"):
#         return
#     user_id = "U07AD6RKUBW"
#     user_info = app.client.users_info(user=user_id)
#     welcome = llm.create(
#         model="gpt-4o-mini-2024-07-18",
#         messages=[llm.systemp(llm.get("prompts/welcome.md").format(info=user_info.data["user"], datetime=datetime.datetime.now().isoformat()))],
#         max_tokens=300
#     ).choices[0].message.content
#     say(welcome)


def main():
    handler = SocketModeHandler(app, app_token=os.environ.get("SLACK_APP_TOKEN"))
    handler.start()

if __name__ == "__main__":
    main()
