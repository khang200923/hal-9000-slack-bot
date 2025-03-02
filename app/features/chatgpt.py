import os
from dotenv import load_dotenv
import llm
from slack_bolt import App

load_dotenv('..')

def chat(app: App):
    # @app.command("/halchat")
    def handle_chat(ack, command, say):
        ack()
        if command["user_id"] != os.getenv("THE_CREATOR_ID"):
            ack()
            say(f"<@{command['user_id']}> is not authorized to use /halchat. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere.")
            return
        res = llm.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[llm.userp(command["text"])],
            max_tokens=3000
        ).choices[0].message.content
        say(f"<@{os.getenv('THE_CREATOR_ID')}> asks \"{command['text']}\". HAL says:\n\n{res}")
    return handle_chat

def feature(app: App):
    app.command("/halchat")(chat(app))

    print("ChatGPT feature enabled.")
