import importlib
from openai import OpenAI
import re
import string
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
tokens = importlib.import_module("tokens")

ai_client = OpenAI(
    api_key=tokens.open_ai_key,
)

oauth_settings = OAuthSettings(
    client_id=tokens.client_id,
    client_secret=tokens.client_secret,
    scopes=["groups:history", "groups:read", "groups:write", "groups:write.invites", "reactions:read", "reactions:write"],
    installation_store=FileInstallationStore(base_dir="./data/installations"),
    state_store=FileOAuthStateStore(expiration_seconds=600, base_dir="./data/states")
)

app = App(
    signing_secret=tokens.client_signing_secret,
    oauth_settings=oauth_settings
)

MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December"
]
def should_react(client, event, logger):
  if "channel_type" in event.keys() and event["channel_type"] == "im":
    return False
  if "thread_ts" not in event.keys():
    return True
  if ("subtype" in event and event["subtype"] == "thread_broadcast"):
    return True
  # get parent message from thread_ts and check if it's the welcome message asking for intros in thread
  try:
    parent = client.conversations_replies(
      channel=event["channel"],
      ts=event["thread_ts"],
      limit=1,
    )
    parent_message = parent["messages"][0]["text"]
    # we want to emoji react to introduction messages in the welcome thread
    if parent_message.startswith("Welcome to"):
      words = parent_message.split()
      if len(words) > 3 and words[2].translate(str.maketrans('', '', string.punctuation)) in MONTHS:
        return True
  except Exception as e:
    logger.error(f"Error checking if threaded message is an intro: {repr(e)}")
  return False

@app.event("message")
def emoji_react(client, event, logger):
  if "text" in event.keys():
    logger.error(f"{event['text']}")
    logger.error(f"type of this event is {event['type']}")
    logger.error(f"channel of this event is {event['channel']}")
    logger.error(f"channel type of this event is {event['channel_type']}")
    logger.error(f"keys {event.keys()}")
  if should_react(client, event, logger):
    try:
      chat_completion = ai_client.chat.completions.create(
          messages=[
            {
              "role": "system",
              "content": "You are a intelligent assistant. You respond to all of the following messages with a single line representing four unique emojis, formatted for Slack. The emojis should represent things mentioned in the messages, with only zero or one emojis representing sentiment. Note that text surrounded by ~ or where the line starts with a negative emoji like :no_pedestrians: means that the task mentioned there was not completed - please exclude these lines from your emoji output. If the messages express deep sadness or high stress, please use :people_hugging: to express comfort instead of something more specific for that part of the text. For example if someone's relative died please react with a hug instead of with an emoji representing the relative or death. Also, please use ungendered emojis, for example, :cook: is preferred over :female-cook: or :male-cook:",
            }, 
            {
              "role": "user",
              "content": event["text"]
            }, 
          ],
          model="gpt-4",
      )
      reply = chat_completion.choices[0].message.content
      print(f"{reply}")
      reply = reply.strip().strip(":")
      emojis = re.split(r':\s*:*', reply)
      for emoji in emojis:
        try:
          client.reactions_add(
            channel=event["channel"],
            timestamp=event["ts"],
            name=f"{emoji}",
          )
        except Exception as e:
          logger.error(f"Error publishing {emoji} emoji react: {repr(e)}")
    except Exception as e:
      logger.error(f"Error getting emojis from OpenAI: {repr(e)}")

# Ready? Start your app!
if __name__ == "__main__":
    app.start(port=3000)
