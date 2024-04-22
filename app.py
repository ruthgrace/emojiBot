import tokens

from openai import OpenAI
import os
# Use the package we installed
from slack_bolt import App
ai_client = OpenAI(
    api_key=tokens.open_ai_key,
)

# Initialize your app with your bot token and signing secret
app = App(
    token=tokens.bot_token,
    signing_secret=tokens.bot_signing_secret
)

# New functionality
@app.event("message")
def emoji_react(client, event, logger):
  try:
    chat_completion = ai_client.chat.completions.create(
        messages=[
          {
            "role": "system",
            "content": "You are a intelligent assistant. You respond to the following messages with a single line representing four unique emojis, formatted for Slack. The emojis should represent things mentioned in the messages, with a focus on nouns and verbs, with one or no emojis representing a sentiment named in the message. If there is an element of the text that is sad or stressed, please use the hug emoji to express comfort instead of something more specific for that part of the text. For example if someone's relative died please react with a hug instead of with an emoji representing the relative or death.",
          }, 
          {
            "role": "user",
            "content": event["text"]
          }, 
        ],
        model="gpt-3.5-turbo",
    )
    reply = chat_completion.choices[0].message.content
    print(f"{reply}")
    app.client.reactions_add(
      channel=event["channel"],
      timestamp=event["ts"],
      name="thumbsup",
      token=tokens.bot_token,
    )
  except Exception as e:
    logger.error(f"Error publishing emoji reacts: {repr(e)}")

# Ready? Start your app!
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))