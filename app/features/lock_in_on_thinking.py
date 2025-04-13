from datetime import datetime, timedelta
import json
import os
import schedule
from dotenv import load_dotenv
from slack_bolt import App

load_dotenv('..')

commitment = None
job = None
time_since_last_message = datetime.now()

# @app.event("message")
def update_time_since_last_message(event):
    if event.get("channel") != os.getenv("NOTES_CHANNEL_ID"):
        return
    global time_since_last_message
    time_since_last_message = datetime.now()

def help_lock_in(say):
    global time_since_last_message
    global commitment
    if datetime.now() - time_since_last_message < timedelta(minutes=10):
        return
    if commitment is None:
        return
    say(f"Hey <@{os.getenv('THE_CREATOR_ID')}>, lock in. Or else...")
    time_since_last_message = datetime.now()

# @app.command("/liot")
def liot_command(ack, say, command):
    ack()
    if command["user_id"] != os.getenv("THE_CREATOR_ID"):
        say(f"<@{command['user_id']}> is not authorized to do /liot. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere.")
        return

    global commitment
    commitment = command["text"]
    say(f"<@{os.getenv('THE_CREATOR_ID')}> commits to lock in on thinking: {commitment}")
    global job
    job = schedule.every(15).seconds.do(lambda: help_lock_in(say))
    schedule.run_pending()

# @app.command("/liot-done")
def liot_done_command(ack, say, command):
    ack()
    if command["user_id"] != os.getenv("THE_CREATOR_ID"):
        say(f"<@{command['user_id']}> is not authorized to do /liot-done. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere.")
        return

    global commitment
    if commitment is None:
        say("No commitment to mark as done.")
        return
    say(f"<@{os.getenv('THE_CREATOR_ID')}> has done locking in on thinking: {commitment}")
    commitment = None
    global job
    if job is not None:
        schedule.cancel_job(job)
        job = None

# @app.command("/liot-status")
def liot_status_command(ack, say, command):
    ack()

    if commitment is None:
        say("No commitment to lock in on thinking.")
    else:
        say(f"<@{os.getenv('THE_CREATOR_ID')}> is currently locking in on thinking: {commitment}. (<@{command['user_id']}> ran /liot-status)")

def feature(app: App):
    app.event("message")(update_time_since_last_message)
    app.command("/liot")(liot_command)
    app.command("/liot-done")(liot_done_command)
    app.command("/liot-status")(liot_status_command)
    print("Lock in on thinking feature enabled.")
