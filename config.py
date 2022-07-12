# .env ファイルをロードして環境変数へ反映
from dotenv import load_dotenv
load_dotenv()

# 環境変数を参照
import os
SLACK_BOT_TOKEN=os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET=os.getenv('SLACK_SIGNING_SECRET')
DATABASE_URL=os.getenv('DATABASE_URL')
