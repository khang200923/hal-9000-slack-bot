import json
import os
import re
import threading
import ast
import time
from dotenv import load_dotenv
import schedule
import llm
from slack_bolt import App

load_dotenv('..')

def display_blocks_from_metadata(metadata):
    title = metadata.get("title", "Untitled")
    done = metadata.get("done", False)
    todos = metadata.get("todos", [])
    blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"TODO list: {title}"
                }
            },
            {
                "type": "divider"
            },
        ]
    if done:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}* is done!"
            }
        })
        blocks.append({
            "type": "divider"
        })
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Undo:"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Undone"
                },
                "value": "undone",
                "action_id": "gtodo_undone_list"
            }
        })
        return blocks
    for i, todo in enumerate(todos):
        desc, done = todo
        full_desc = desc
        if done:
            full_desc = f"~{full_desc}~"
        full_desc = f"{i + 1}. {full_desc}"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": full_desc
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Done" if not done else "Undone"
                },
                "value": f"{i}",
                "action_id": "gtodo_done"
            }
        })
    blocks.append({
        "type": "divider"
    })
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Add a new todo:"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Add"
            },
            "value": "new",
            "action_id": "gtodo_new_todo"
        }
    })
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Mark as done:"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Done"
            },
            "value": "done",
            "action_id": "gtodo_done_list"
        }
    })
    return blocks

# @app.command("/gamed-todo")
def handle_gamed_todo(ack, command, say):
    ack()
    if command["user_id"] != os.getenv("THE_CREATOR_ID"):
        say(f"<@{command['user_id']}> is not authorized to use /gamed_todo. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere.")
        return

    title = command["text"]
    metadata = {"title": title, "done": False, "todos": []}

    say(
        metadata={"event_type": "gtodo", "event_payload": metadata},
        blocks=display_blocks_from_metadata(metadata),
        text=f"TODO list: {title}"
    )

# @app.action(gtodo_new_todo)
def handle_new_todo(ack, body, client):
    ack()
    if body["user"]["id"] != os.getenv("THE_CREATOR_ID"):
        client.chat_postMessage(
            channel=body["channel"]["id"],
            thread_ts=body["message"]["ts"],
            text=f"<@{body['user']['id']}> is not authorized to do gtodo_new_todo. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere."
        )
        return
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "gtodo_new_todo",
            "title": {
                "type": "plain_text",
                "text": "New TODO"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "desc",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "desc"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Description"
                    }
                }
            ],
            "private_metadata": json.dumps({
                "channel_id": body["channel"]["id"],
                "message_ts": body["message"]["ts"],
            })
        }
    )

# @app.view("gtodo_new_todo")
def handle_new_todo_view(ack, body, client):
    print("debug")
    ack()
    view_metadata = body["view"]["private_metadata"]
    view_metadata = json.loads(view_metadata)
    channel_id = view_metadata["channel_id"]
    message_ts = view_metadata["message_ts"]
    desc = body["view"]["state"]["values"]["desc"]["desc"]["value"]
    metadata = client.conversations_history(channel=channel_id, latest=message_ts, limit=1, include_all_metadata=True)["messages"][0]["metadata"]["event_payload"]
    todos = metadata["todos"]
    todos.append([desc, False])
    metadata["todos"] = todos
    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        metadata={"event_type": "gtodo", "event_payload": metadata},
        blocks=display_blocks_from_metadata(metadata)
    )

# @app.action(gtodo_done)
def handle_done(ack, body, client):
    ack()
    if body["user"]["id"] != os.getenv("THE_CREATOR_ID"):
        client.chat_postMessage(
            channel=body["channel"]["id"],
            thread_ts=body["message"]["ts"],
            text=f"<@{body['user']['id']}> is not authorized to do gtodo_done. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere."
        )
        return
    metadata = body["message"]["metadata"]["event_payload"]
    todos = metadata["todos"]
    i = int(body["actions"][0]["value"])
    todos[i][1] = not todos[i][1]
    metadata["todos"] = todos
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        metadata={"event_type": "gtodo", "event_payload": metadata},
        blocks=display_blocks_from_metadata(metadata)
    )

# @app.action(gtodo_done_list)
def handle_done_list(ack, body, client):
    ack()
    if body["user"]["id"] != os.getenv("THE_CREATOR_ID"):
        client.chat_postMessage(
            channel=body["channel"]["id"],
            thread_ts=body["message"]["ts"],
            text=f"<@{body['user']['id']}> is not authorized to do gtodo_done_list. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere."
        )
        return
    metadata = body["message"]["metadata"]["event_payload"]
    metadata["done"] = True
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        metadata={"event_type": "gtodo", "event_payload": metadata},
        blocks=display_blocks_from_metadata(metadata)
    )

# @app.action(gtodo_undone_list)
def handle_undone_list(ack, body, client):
    ack()
    if body["user"]["id"] != os.getenv("THE_CREATOR_ID"):
        client.chat_postMessage(
            channel=body["channel"]["id"],
            thread_ts=body["message"]["ts"],
            text=f"<@{body['user']['id']}> is not authorized to do gtodo_undone_list. Yo <@{os.getenv('THE_CREATOR_ID')}> c'mere."
        )
        return
    print(body, body["message"])
    metadata = body["message"]["metadata"]["event_payload"]
    metadata["done"] = False
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        metadata={"event_type": "gtodo", "event_payload": metadata},
        blocks=display_blocks_from_metadata(metadata)
    )

def feature(app: App):
    app.command("/gamed-todo")(handle_gamed_todo)
    app.action("gtodo_new_todo")(handle_new_todo)
    app.view("gtodo_new_todo")(handle_new_todo_view)
    app.action("gtodo_done")(handle_done)
    app.action("gtodo_done_list")(handle_done_list)
    app.action("gtodo_undone_list")(handle_undone_list)

    print("Gamed todo feature enabled.")
