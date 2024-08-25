import telebot
from telebot import types
import fitz  # PyMuPDF
from gtts import gTTS
import os

# Initialize the bot
bot_token = "7478578310:AAEM9Zb-NXbeF1sy9zm6EN2bTcgNs6BaomQ"
bot = telebot.TeleBot(bot_token)

# Default settings
user_language = {}
user_voice = {}
user_page_range = {}
user_files = {}

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("📄 Convert PDF to Audio")
    item2 = types.KeyboardButton("🌐 Change Language")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

# Handle text messages (e.g., button presses)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id

    if message.text == "📄 Convert PDF to Audio":
        bot.send_message(chat_id, "Please send the PDF file you want to convert.")

    elif message.text == "🌐 Change Language":
        change_language(chat_id)

    # Handling Support buttons
    elif message.text == "☕ Buy Me Coffee":
        bot.send_message(chat_id, "🏧Account: 2016413995\n🏦Bank: Kuda Microfinance Bank")
    elif message.text == "💵 Sponsor Next Project":
        bot.send_message(chat_id, "🏧Account: 2016413995\n🏦Bank: Kuda Microfinance Bank")
    elif message.text == "🗨️ Talk To Developer":
        markup = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton("DM StrongNation", url="https://t.me/enochs_world")
        markup.add(contact_button)
        bot.send_message(chat_id, "Send a private message to the real Developer of this PDF2MP3 BOT:", reply_markup=markup)

    # Handle back command
    elif message.text == "/back":
        send_welcome(message)

# Function to change language
def change_language(chat_id):
    markup = types.InlineKeyboardMarkup()
    lang_buttons = [
        types.InlineKeyboardButton("English", callback_data='lang_en'),
        types.InlineKeyboardButton("Spanish", callback_data='lang_es'),
        types.InlineKeyboardButton("French", callback_data='lang_fr'),
        types.InlineKeyboardButton("German", callback_data='lang_de')
    ]
    markup.add(*lang_buttons)
    bot.send_message(chat_id, "Select your preferred language:", reply_markup=markup)

# Handle language selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_language(call):
    lang_code = call.data.split('_')[1]
    user_language[call.message.chat.id] = lang_code
    select_voice(call.message.chat.id)

# Function to select voice (man or woman)
def select_voice(chat_id):
    markup = types.InlineKeyboardMarkup()
    voice_buttons = [
        types.InlineKeyboardButton("Man", callback_data='voice_man'),
        types.InlineKeyboardButton("Woman", callback_data='voice_woman')
    ]
    markup.add(*voice_buttons)
    bot.send_message(chat_id, "Select the voice type:", reply_markup=markup)

# Handle voice selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('voice_'))
def callback_voice(call):
    voice_type = call.data.split('_')[1]
    user_voice[call.message.chat.id] = voice_type
    process_pdf(call.message.chat.id)

# Handle PDF file reception
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.document.file_id)
    file = bot.download_file(file_info.file_path)

    file_path = f"{message.document.file_name}"
    user_files[chat_id] = file_path

    with open(file_path, 'wb') as f:
        f.write(file)

    bot.send_message(chat_id, "Please enter the page range you want to convert (e.g., 1-3 or 5):")
    bot.register_next_step_handler(message, handle_page_range)

# Handle page range selection
def handle_page_range(message):
    try:
        page_range = message.text.strip()
        user_page_range[message.chat.id] = page_range
        change_language(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, "Invalid input. Please try again.")
        bot.register_next_step_handler(message, handle_page_range)

# Function to process PDF and convert to audio
def process_pdf(chat_id):
    file_path = user_files.get(chat_id, None)
    if not file_path or not os.path.exists(file_path):
        bot.send_message(chat_id, "No PDF file found. Please send the PDF again.")
        return

    bot.send_message(chat_id, "Processing the PDF...")

    try:
        page_range = user_page_range.get(chat_id, None)
        pdf_text = convert_pdf_to_text(file_path, page_range)
        if pdf_text:
            bot.send_message(chat_id, "Converting text to speech...")
            convert_text_to_speech(chat_id, pdf_text, user_language.get(chat_id, 'en'), user_voice.get(chat_id, 'man'))
        else:
            bot.send_message(chat_id, "Sorry, I couldn't extract text from this PDF.")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        user_files.pop(chat_id, None)

    # Show options for supporting or contacting the developer
    show_support_options(chat_id)

# Function to convert PDF to text with page range support
def convert_pdf_to_text(pdf_path, page_range):
    pdf_text = ""
    with fitz.open(pdf_path) as doc:
        if '-' in page_range:
            start, end = map(int, page_range.split('-'))
            for page_num in range(start-1, end):
                pdf_text += doc.load_page(page_num).get_text()
        else:
            page_num = int(page_range) - 1
            pdf_text += doc.load_page(page_num).get_text()
    return pdf_text.strip()

# Function to convert text to speech
def convert_text_to_speech(chat_id, text, lang_code='en', voice='man'):
    tts = gTTS(text=text, lang=lang_code, slow=False)
    audio_file = f"{chat_id}_output.mp3"
    tts.save(audio_file)

    with open(audio_file, 'rb') as audio:
        bot.send_audio(chat_id, audio)

    os.remove(audio_file)

# Function to show support options
def show_support_options(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("☕ Buy Me Coffee")
    item2 = types.KeyboardButton("💵 Sponsor Next Project")
    item3 = types.KeyboardButton("🗨️ Talk To Developer")
    item4 = types.KeyboardButton("🔙 Back")
    markup.add(item1, item2, item3, item4)
    bot.send_message(chat_id, "Thank you for using the service! How would you like to support or contact us?", reply_markup=markup)

# Handle specific commands triggered by buttons
@bot.message_handler(commands=['buycoffee', 'sponsorproject', 'talktodeveloper'])
def handle_commands(message):
    if message.text == "/buycoffee" or message.text == "/sponsorproject":
        bot.send_message(message.chat.id, "🏧Account: 2016413995\n🏦Bank: Kuda Microfinance Bank")
    elif message.text == "/talktodeveloper":
        markup = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton("DM StrongNation", url="https://t.me/enochs_world")
        markup.add(contact_button)
        bot.send_message(message.chat.id, "Send a private message to the real Developer of this PDF2MP3 BOT:", reply_markup=markup)

# Start the bot
bot.polling()
