import os
# Use the package we installed
from slack_bolt import App
import config
import psycopg2

DATABASE_URL='postgresql://postgre:password@solve_db:5432/postgre'

connection = psycopg2.connect(DATABASE_URL)
cur = connection.cursor()

app = App(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET
)

# def main():
#   # connect()
#   # print(connect())
#   cur.execute('SELECT * FROM thread')
#   # data = abc().fetchall()
#   for item in cur:
#     print(item)

# 疑問を送る送るチャンネル
channel_id = "C03KE0P7U4D"

# ****************************************************************
# events
# ****************************************************************

# ホームタブに表示
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    client.views_publish(
      user_id=event["user"],
      view={
        "type": "home",
        "callback_id": "home_view",
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
              "text": "疑問を投稿しよう",
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
                  "text": "投稿する",
                  "emoji": True
                },
                "style": "primary",
                "value": "send_question",
                "action_id": "send_question"
              }
            ]
          }
        ]
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

 # result = client.chat_postMessage(
    #   channel=channel_id,
    #   blocks=[
    #     {
    #       "type": "section",
    #       "text": {
    #         "type": "plain_text",
    #         "text": "message",
    #         "emoji": True
    #       }
    #     },
    #     {
    #       "type": "actions",
    #       "elements": [
    #         {
    #           "type": "button",
    #           "text": {
    #             "type": "plain_text",
    #             "text": "解決した",
    #             "emoji": True
    #           },
    #           "value": "click_me_123",
    #           "action_id": "open_done_modal"
    #         },
    #         {
    #           "type": "button",
    #           "text": {
    #             "type": "plain_text",
    #             "text": "返信する",
    #             "emoji": True
    #           },
    #           "style": "primary",
    #           "value": "click_me_123",
    #           "action_id": "open_reply_modal"
    #         }
    #       ]
    #     }
    #   ]
    # )

# スレッドに返信があった場合にDMを送る
@app.message("")
def send_dm(ack, body, client, logger):
  ack()

  # print(body)
  sender_id = body['event']['user']
  res = client.conversations_open(users= sender_id)
  dm_id = res['channel']['id']
  thread_ts = body['event']['thread_ts']
  cur.execute("SELECT * FROM thread WHERE thread_id = '%s'" % (thread_ts))
  getters = []
  for item in cur:
    getters.append(item)
  # print(type(getters[0]))
  getter_id = getters[0][1]
  # cur.close()

  thread_last_message = body['event']['blocks'][0]['elements'][0]['elements'][0]['text']
  # getter = cur

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
    sender_id = result['message']['user']
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
        "private_metadata": thread_first_ts,
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

  print(body)

  message_block_id = body['view']['blocks'][0]['block_id']
  message = body['view']['state']['values'][message_block_id]['plain_text_input-action']['value']

  try:
    result = client.chat_postMessage(
      channel=channel_id,
      text=message
    )
    logger.info(result)

  except Exception as e:
    logger.error(f"Error posting message: {e}")


if __name__ == "__main__":
  # SocketModeHandler(app, config.SLACK_BOT_TOKEN).start()
  app.start(port=int(os.environ.get("PORT", 3000)))
  # main()
