import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import pytz
import psycopg2

import features

load_dotenv()
app = App()
db: psycopg2.extensions.connection = None
cursor: psycopg2.extensions.cursor = None

def core():
    features.welcome.feature(app)
    features.gamed_todo.feature(app)
    features.chatgpt.feature(app)
    features.lock_in_on_thinking.feature(app)
    handler = SocketModeHandler(app, app_token=os.environ.get("SLACK_APP_TOKEN"))
    handler.start()

def main():
    global db, cursor
    db = psycopg2.connect(os.getenv("POSTGRESQL_CONNECTION_STRING"))
    cursor = db.cursor()
    core()

if __name__ == "__main__":
    main()
