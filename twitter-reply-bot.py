import tweepy
from datetime import datetime, timedelta
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import schedule
import time
import os

# Helpful when testing locally
from dotenv import load_dotenv
load_dotenv()

# Load your Twitter API keys
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "YourKey")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "YourKey")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "YourKey")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "YourKey")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "YourKey")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YourKey")

# TwitterBot class
class TwitterBot:
    def __init__(self):
        self.twitter_api = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN,
                                         consumer_key=TWITTER_API_KEY,
                                         consumer_secret=TWITTER_API_SECRET,
                                         access_token=TWITTER_ACCESS_TOKEN,
                                         access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                                         wait_on_rate_limit=True)
        self.twitter_me_id = self.get_me_id()
        self.tweet_response_limit = 35

        # Initialize the language model
        self.llm = ChatOpenAI(temperature=.5, openai_api_key=OPENAI_API_KEY, model_name='gpt-4')

        # For statics tracking for each run
        self.mentions_found = 0
        self.mentions_replied = 0
        self.mentions_replied_errors = 0

    # Returns the ID of the authenticated user for tweet creation purposes
    def get_me_id(self):
        return self.twitter_api.get_me()[0].id

    def respond_to_mentions(self):
        mentions = self.get_mentions()

        # If no mentions, just return
        if not mentions:
            print("No mentions found")
            return
        
        self.mentions_found = len(mentions)

        for mention in mentions[:self.tweet_response_limit]:
            # Getting the mention's conversation tweet
            mentioned_conversation_tweet = self.get_mention_conversation_tweet(mention)
            
            # If the mention *is* the conversation, skip it and don't respond
            if mentioned_conversation_tweet.id != mention.id:
                self.respond_to_mention(mention, mentioned_conversation_tweet)
        return True

    # (Other methods remain unchanged...)

    def respond_to_mention(self, mention, mentioned_conversation_tweet):
        response_text = self.generate_response(mentioned_conversation_tweet.text)
        
        # Try and create the response to the tweet
        try:
            self.twitter_api.create_tweet(text=response_text, in_reply_to_tweet_id=mention.id)
            self.mentions_replied += 1
        except Exception as e:
            print(e)
            self.mentions_replied_errors += 1

    # (Other methods remain unchanged...)

    # The main entry point for the bot with some logging
    def execute_replies(self):
        print(f"Starting Job: {datetime.utcnow().isoformat()}")
        self.respond_to_mentions()
        print(f"Finished Job: {datetime.utcnow().isoformat()}, Found: {self.mentions_found}, Replied: {self.mentions_replied}, Errors: {self.mentions_replied_errors}")

# The job that we'll schedule to run every X minutes
def job():
    print(f"Job executed at {datetime.utcnow().isoformat()}")
    bot = TwitterBot()
    bot.execute_replies()

if __name__ == "__main__":
    # Schedule the job to run every 6 minutes
    schedule.every(6).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
