from datetime import datetime, timedelta
import os
import re
import threading
import time
from dotenv import load_dotenv
import schedule
import llm
import pytz
import psycopg2
from slack_bolt import App

load_dotenv('..')

tz = pytz.timezone(os.environ.get("TIMEZONE"))

def db_init(db: psycopg2.extensions.connection, cursor: psycopg2.extensions.cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id SERIAL PRIMARY KEY,
            text TEXT,
            creation_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMPTZ DEFAULT NULL,
            done BOOLEAN DEFAULT FALSE,
            ts TEXT DEFAULT NULL
        )""")
    db.commit()

def to_time(value: str) -> datetime:
    value = value.strip()
    if value.lower().startswith("in-sec"):
        return datetime.now(tz) + timedelta(seconds=int(value[6:])+5)
    if value.lower().startswith("in-min"):
        return datetime.now(tz) + timedelta(minutes=int(value[6:]), seconds=5)
    if value.lower().startswith("in-hour"):
        return datetime.now(tz) + timedelta(hours=int(value[7:]), seconds=5)
    if value.lower().startswith("in-day"):
        return datetime.now(tz) + timedelta(days=int(value[6:]), seconds=5)
    if value.lower().startswith("in"):
        return tz.localize(datetime.fromisoformat(value[2:].strip()))
    if value.lower().startswith("at"):
        hour, minute = value[2:].split(":")
        return datetime.now(tz).replace(hour=int(hour), minute=int(minute))
    return tz.localize(datetime.fromisoformat(value.strip()))

def mention(app: App, db: psycopg2.extensions.connection, cursor: psycopg2.extensions.cursor):
    # @app.event("app_mention")
    def handle_mention(event, say):
        print("debug handle_mention", event["ts"])

        # I think this event subscription has a bug here so I'm adding this
        cursor.execute("SELECT 1 FROM todos WHERE ts = %s", (event["ts"],))
        if cursor.fetchone() is not None:
            return

        text = event["text"]
        if "todo:add" in text.lower():
            content, end_time = re.search("todo:add[^]+", text).group()[8:].split(" / ")
            end_time = to_time(end_time)
            todo_add(app, db, cursor, content, datetime.now(), event["ts"])
            say("Todo successfully added", thread_ts=event["ts"])
        if "todo:ls" in text.lower():
            cursor.execute("SELECT (text, creation_time, end_time, done) FROM todos")
            todos = cursor.fetchall()
            say("Here are your unfinished todos:")
            for todo in todos:
                if todo[3]:
                    continue
                say(f"{todo[0]} (created at {todo[1]}, due at {todo[2]})")
    return handle_mention

def todo_add(app: App, db: psycopg2.extensions.connection, cursor: psycopg2.extensions.cursor, text: str, end_time: datetime, ts: str):
    cursor.execute("INSERT INTO todos (text, end_time, ts) VALUES (%s, %s, %s)", (text, end_time, ts))
    db.commit()

def check_todos(app: App, db: psycopg2.extensions.connection, cursor: psycopg2.extensions.cursor):
    def job():
        print("debug check_todos")
        cursor.execute("SELECT id, text, creation_time, end_time, ts FROM todos")
        todos = cursor.fetchall()
        def condition(todo, a: timedelta, b: timedelta) -> bool:
            return (todo[3] - todo[2] >= a) & (todo[3] < datetime.now(tz) + b)
        for todo in todos:
            if condition(todo, timedelta(days=7), timedelta(days=2)):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due in 2 days.", thread_ts=todo[4])
            if condition(todo, timedelta(days=1), timedelta(hours=6)):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due in 6 hours.", thread_ts=todo[4])
            if condition(todo, timedelta(hours=3), timedelta(hours=1)):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due in 1 hour.", thread_ts=todo[4])
            if condition(todo, timedelta(hours=1), timedelta(minutes=15)):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due in 15 minutes.", thread_ts=todo[4])
            if condition(todo, timedelta(minutes=10), timedelta(minutes=5)):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due in 5 minutes.", thread_ts=todo[4])
            if condition(todo, timedelta(minutes=1), timedelta(seconds=30)):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due in 30 seconds.", thread_ts=todo[4])
            if todo[3] < datetime.now(tz):
                app.client.chat_postMessage(channel=os.environ.get("THE_CHANNEL_ID"), text=f"Todo {todo[1]} is due now.", thread_ts=todo[4])
                cursor.execute("UPDATE todos SET done = TRUE WHERE id = %s", (todo[0],))
                db.commit()
    schedule.every(5).seconds.do(job)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(5)

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

def feature(app: App, db: psycopg2.extensions.connection, cursor: psycopg2.extensions.cursor):
    db_init(db, cursor)
    app.event("app_mention")(mention(app, db, cursor))
    check_todos(app, db, cursor)

    print("Todos feature enabled.")
