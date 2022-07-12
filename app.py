import os
# Use the package we installed
from slack_bolt import App
import config
import psycopg2
import json
import tkinter as tk
import tkinter.filedialog
import glob

connection = psycopg2.connect(config.DATABASE_URL)
cur = connection.cursor()

app = App(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET
)

# 疑問を送る送るチャンネル
channel_id = "C03KE0P7U4D"

# ****************************************************************
# events
# ****************************************************************

# ホームタブに表示
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  json_open = open('blocks/home_opened.json', 'r')
  json_load = json.load(json_open)

  try:
    client.views_publish(
      user_id=event["user"],
      view=json_load
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

# スレッドに返信があった場合にDMを送る
@app.message("")
def send_dm(ack, body, client, logger):
  ack()

  # print(body)
  sender_id = body['event']['user']
  thread_ts = body['event']['thread_ts']
  cur.execute("SELECT * FROM thread WHERE thread_id = '%s'" % (thread_ts))
  getters = []
  for item in cur:
    getters.append(item)
  getter_id = getters[0][1]
  print(getter_id)
  res = client.conversations_open(users= getter_id)
  dm_id = res['channel']['id']
  thread_first_message = getters[0][3]

  thread_last_message = body['event']['blocks'][0]['elements'][0]['elements'][0]['text']

  if body['event']['thread_ts'] != None:
    try:
      result = client.chat_postMessage(
        channel=dm_id,
        blocks=[
          {
            "type": "section",
            "text": {
              "type": "plain_text",
              "text": thread_last_message,
              "emoji": True
            }
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "解決した",
                  "emoji": True
                },
                "value": "click_me_123",
                "action_id": "open_done_modal"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "返信する",
                  "emoji": True
                },
                "style": "primary",
                "value": "click_me_123",
                "action_id": "open_reply_modal"
              }
            ]
          }
        ],
        metadata={
          "event_type": "dm",
          "event_payload": {
            "id": sender_id,
            "title": thread_ts
          }
        }
      )
      logger.info(result)

      # スレッドのステータスを回答中に変更
      client.chat_update(
        channel=channel_id,
        ts=thread_ts,
        blocks=[
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": thread_first_message
            },
            "accessory": {
              "type": "button",
              "text": {
                "type": "plain_text",
                "text": "回答中",
                "emoji": True
              },
              "style": "primary",
              "value": "click_me_123",
              "action_id": "button-action"
            }
          }
        ]
      )

    except Exception as e:
      logger.error(f"Error posting message: {e}")


# ****************************************************************
# actions
# ****************************************************************

# 疑問を送る
@app.action("send_question")
def send_question(ack, body, client, logger):
  ack()

  message_block_id = body['view']['blocks'][0]['block_id']
  message = body['view']['state']['values'][message_block_id]['plain_text_input-action']['value']
  sender_id = body['user']['id']

  json_open = open('blocks/home_sended.json', 'r')
  json_load = json.load(json_open)

  try:
    # Call the chat.postMessage method using the WebClient
    result = client.chat_postMessage(
      channel=channel_id,
      blocks=[
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": message
          },
          "accessory": {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "未回答",
              "emoji": True
            },
            "style": "danger",
            "value": "click_me_123",
            "action_id": "open_reply_modal"
          }
        }
      ]
    )

    client.views_publish(
      user_id=sender_id,
      view=json_load
    )
    logger.info(result)
    thread_ts = result['ts']
    sql = "INSERT INTO thread (user_id,thread_id,messages,token) VALUES('%s', '%s', '%s', null);" % (sender_id, thread_ts, message)
    cur.execute(sql)
    cur.execute('SELECT * FROM thread')
    for item in cur:
      print(item)

    cur.commit()

  except Exception as e:
    logger.error(f"Error posting message: {e}")

@app.action("select_files")
def select_files(ack, body, logger):
  ack()
  logger.info(body)

@app.action("plain_text_input-action")
def send_question(ack, body, client, logger):
  ack()

  message_block_id = body['view']['blocks'][0]['block_id']
  message = body['view']['state']['values'][message_block_id]['plain_text_input-action']['value']

  try:
    # Call the chat.postMessage method using the WebClient
    result = client.chat_postMessage(
      channel=channel_id,
      blocks=[
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": message
          },
          "accessory": {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "未回答",
              "emoji": True
            },
            "style": "danger",
            "value": "click_me_123",
            "action_id": "open_reply_modal"
          }
        }
      ]

    )
    logger.info(result)
    sender_id = body['user']['id']
    thread_ts = result['ts']
    sql = "INSERT INTO thread (user_id,thread_id,messages,token) VALUES('%s', '%s', '%s', null);" % (sender_id, thread_ts, message)
    cur.execute(sql)
    cur.execute('SELECT * FROM thread')
    for item in cur:
      print(item)

    cur.commit()

  except Exception as e:
    logger.error(f"Error posting message: {e}")

# 返信のモーダルを開く
@app.action("open_reply_modal")
def open_reply_modal(ack, body, client, logger):
  ack()

  thread_ts = body['message']['metadata']['event_payload']['title']
  thread = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
          )
  thread_first_ts = thread['messages'][0]['ts']

  try:
    result = client.views_open(
      trigger_id=body["trigger_id"],
      view={
        "type": "modal",
        "callback_id": "reply_modal",
        "title": {
          "type": "plain_text",
          "text": "ソルブ",
          "emoji": True
        },
        "submit": {
          "type": "plain_text",
          "text": "送信",
          "emoji": True
        },
        "close": {
          "type": "plain_text",
          "text": "キャンセル",
          "emoji": True
        },
        "blocks": [
          {
            "type": "input",
            "element": {
              "type": "plain_text_input",
              "multiline": True,
              "action_id": "plain_text_input-action"
            },
            "label": {
              "type": "plain_text",
              "text": "返信しよう",
              "emoji": True
            }
          }
        ],
        "private_metadata": thread_first_ts,
      },
    )
    logger.info(result)

  except Exception as e:
    logger.error("Error creating conversation: {}".format(e))

# 完了のモーダルを開く
@app.action("open_done_modal")
def open_done_modal(ack, body, client, logger):
  ack()

  trigger_id = body['trigger_id']
  thread_ts = body['message']['metadata']['event_payload']['title']
  thread = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
          )
  thread_first_ts = thread['messages'][0]['ts']
  sender_id = body['message']['metadata']['event_payload']['id']

  try:
    result = client.views_open(
      trigger_id=trigger_id,
      view={
        "type": "modal",
        "callback_id": "done_modal",
        "title": {
          "type": "plain_text",
          "text": "ソルブ",
          "emoji": True
        },
        "submit": {
          "type": "plain_text",
          "text": "投稿する",
          "emoji": True
        },
        "close": {
          "type": "plain_text",
          "text": "キャンセル",
          "emoji": True
        },
        "blocks": [
          {
            "type": "input",
            "element": {
              "type": "plain_text_input",
              "multiline": True,
              "action_id": "plain_text_input-action"
            },
            "label": {
              "type": "plain_text",
              "text": "感謝を送ろう",
              "emoji": True
            }
          }
        ],
        "private_metadata":  json.dumps({
          "thread_id": "%s" % (thread_first_ts),
          "sender_id": sender_id
        }),
      },
    )
    logger.info(result)

  except Exception as e:
    logger.error("Error creating conversation: {}".format(e))

# ****************************************************************
# view
# ****************************************************************

# 返信のモーダルから送信
@app.view("reply_modal")
def handle_view_events(ack, body, logger, client):
  ack()

  print(body)
  thread_ts = body['view']['private_metadata']
  thread = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
          )
  thread_first_ts = thread['messages'][0]['ts']
  message_block_id = body['view']['blocks'][0]['block_id']
  message = body['view']['state']['values'][message_block_id]['plain_text_input-action']['value']

  try:
    result = client.chat_postMessage(
      channel=channel_id,
      text=message,
      thread_ts=thread_first_ts
    )
    logger.info(result)

  except Exception as e:
    logger.error(f"Error posting message: {e}")

# 完了のモーダルから送信
@app.view("done_modal")
def handle_view_events(ack, body, logger, client):
  ack()

  # print(body)

  message_block_id = body['view']['blocks'][0]['block_id']
  message = body['view']['state']['values'][message_block_id]['plain_text_input-action']['value']
  thread_ts = json.loads(body['view']['private_metadata'])['thread_id']
  print(thread_ts)
  thread = client.conversations_replies(
    channel=channel_id,
    ts=thread_ts
  )
  thread_first_ts = thread['messages'][0]['ts']
  thread_first_message = thread['messages'][0]['blocks'][0]['text']['text']

  sender_id = json.loads(body['view']['private_metadata'])['sender_id']
  solver = client.users_info(user= sender_id)['user']['profile']['display_name']

  try:
    result = client.chat_postMessage(
      channel=channel_id,
      text=message,
      thread_ts=thread_first_ts
    )
    logger.info(result)

    # スレッドのステータスを回答中に変更
    client.chat_update(
      channel=channel_id,
      ts=thread_ts,
      blocks=[
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": thread_first_message
          },
          "accessory": {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "%sさんが解決" % (solver),
              "emoji": True
            },
            "value": "click_me_123",
            "action_id": "button-action"
          }
        }
      ]
    )

  except Exception as e:
    logger.error(f"Error posting message: {e}")


if __name__ == "__main__":
  app.start(port=int(os.environ.get("PORT", 3000)))
