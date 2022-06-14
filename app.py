import os
# Use the package we installed
from slack_bolt import App
import config
import psycopg2

DATABASE_URL='postgresql://postgre:password@solve_db:5432/postgres'

app = App(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET
)

def main():
  cursor = psycopg2.connect(DATABASE_URL)
  print(cursor)

# 疑問を送る送るチャンネル
channel_id = "C03FQHH6VGA"

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

# スレッドに返信があった場合にDMを送る
@app.event("message")
def send_dm(ack, body, client, logger):
  ack()

  print(body)

  try:
    result = client.chat_postMessage(
      channel=channel_id,
      blocks=[
        {
          "type": "section",
          "text": {
            "type": "plain_text",
            "text": "message",
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
      ]
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
  # user = body['user']['id']
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

  except Exception as e:
    logger.error(f"Error posting message: {e}")

# 返信のモーダルを開く
@app.action("open_reply_modal")
def open_reply_modal(ack, body, client, logger):
  ack()

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
      },
    )
    logger.info(result)

  except Exception as e:
    logger.error("Error creating conversation: {}".format(e))

# 完了のモーダルを開く
@app.action("open_done_modal")
def open_done_modal(ack, body, client, logger):
  ack()

  try:
    result = client.views_open(
      trigger_id=body["trigger_id"],
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
  app.start(port=int(os.environ.get("PORT", 3000)))
  # main()
