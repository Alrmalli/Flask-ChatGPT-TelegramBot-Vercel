import logging
import os
import telegram
from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters
import openai

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set the language of the chat bot
chat_language = os.getenv("INIT_LANGUAGE", default="en")

# Set the message limit and language table
MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default=20))
LANGUAGE_TABLE = {
    "zh": "Hello!",
    "en": "Hello!",
    "jp": "Hello!"
}

# Class to handle prompts
class Prompts:
    def __init__(self):
        self.msg_list = []
        self.msg_list.append(f"AI:{LANGUAGE_TABLE[chat_language]}")
	    
    def add_msg(self, new_msg):
        if len(self.msg_list) >= MSG_LIST_LIMIT:
            self.remove_msg()
        self.msg_list.append(new_msg)
	
    def remove_msg(self):
        self.msg_list.pop(0)
	
    def generate_prompt(self):
        return '\n'.join(self.msg_list)	
	
# Class for the ChatGPT model  
class ChatGPT:  
    def __init__(self):
        self.prompt = Prompts()
        self.model = os.getenv("OPENAI_MODEL", default="text-davinci-003")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default=0))
        self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default=0))
        self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", default=0.6))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default=240))
	
    def get_response(self):
        response = openai.Completion.create(
	            model=self.model,
	            prompt=self.prompt.generate_prompt(),
	            temperature=self.temperature,
	            frequency_penalty=self.frequency_penalty,
	            presence_penalty=self.presence_penalty,
	            max_tokens=self.max_tokens
                )
        
        print("AI response:")        
        print(response['choices'][0]['text'].strip())

        print("Original response data from AI:")      
        print(response)
        
        return response['choices'][0]['text'].strip()
	
    def add_msg(self, text):
        self.prompt.add_msg(text)

# Set Telegram bot token
telegram_bot_token = str(os.getenv("TELEGRAM_BOT_TOKEN"))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot with Telegram access token
bot = telegram.Bot(token=telegram_bot_token)

# Function to handle incoming messages
def reply_handler(bot, update):
    # Create instance of ChatGPT
    chatgpt = ChatGPT()        
    
    # Add the user's message to the prompt
    chatgpt.prompt.add_msg(update.message.text)
    
    # Get the AI's response
    ai_reply_response = chatgpt.get_response()
    
    # Reply to the user with the AI's response
    update.message.reply_text(ai_reply_response)


# Route to handle incoming messages
@app.route('/callback', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher to process this message
        dispatcher.process_update(update)
        
    return 'ok'

# Initialize dispatcher for the bot
dispatcher = Dispatcher(bot, None)

# Add handler to process text messages
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

#Start the bot
if __name__ == 'main':
    app.run()
