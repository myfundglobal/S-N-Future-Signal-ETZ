import time
from datetime import datetime, timedelta
import pytz
import telebot
from telebot import types
import yfinance as yf
import pandas as pd

# Token me koi space nahi hona chahiye (bilkul exact yeh likhein)
TOKEN = "8792943982:AAF7hNy8KjZmTeHTgUY4BMgq3qL3ejIaVLA"
bot = telebot.TeleBot(TOKEN)

def get_signal_for_asset(symbol, display_name):
    """Market data fetch karke Support & Resistance ke basis par 1-min signal nikalna"""
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 10:
            return f"❌ Data filhal available nahi hai {display_name} ke liye."
        
        current_price = float(df['Close'].iloc[-1])
        
        # S&R Calculation using Rolling Window
        df['Support'] = df['Low'].rolling(window=5, center=True).min()
        df['Resistance'] = df['High'].rolling(window=5, center=True).max()
        
        support = float(df['Support'].dropna().iloc[-1])
        resistance = float(df['Resistance'].dropna().iloc[-1])
        
        # IST Timezone setup
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        open_time = now_ist.strftime("%H:%M:%S")
        expiry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M:%S")
        
        # Signal Logic
        if abs(current_price - support) < abs(current_price - resistance):
            signal_type = "🟢 CALL (UP) [Support Bounce]"
            level = support
        else:
            signal_type = "🔴 PUT (DOWN) [Resistance Rejection]"
            level = resistance

        msg = (
            f"🎯 **QUOTEX 1-MIN SIGNAL** 🎯\n\n"
            f"📊 **Asset:** `{display_name}`\n"
            f"📈 **Direction:** {signal_type}\n"
            f"⏰ **Open Time:** `{open_time} IST`\n"
            f"⏳ **Expiry Time:** `{expiry_time} IST` (1 Min)\n"
            f"💰 **Entry Price:** `{current_price:.5f}`\n"
            f"🛡️ **Key Level:** `{level:.5f}`\n\n"
            f"⚠️ *Note: Trade with proper risk management.*"
        )
        return msg
    except Exception as e:
        return f"⚠️ Market analyze karne me error aayi: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Jab user /start likhega toh seedha buttons show honge"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🌐 Real Market (EUR/USD, GBP/USD)", callback_data="real_market")
    btn2 = types.InlineKeyboardButton("🪙 Crypto Market (BTC/USD, ETH/USD)", callback_data="crypto_market")
    btn3 = types.InlineKeyboardButton("🔄 OTC Market (Quotex OTC Simulated)", callback_data="otc_market")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(
        message.chat.id,
        "🤖 **Welcome to Pro S&R Trading Bot!**\n\n"
        "Neeche diye gaye options me se apna market select karein:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Button click hone par signal generate karna"""
    bot.answer_callback_query(call.id, "Analyzing market levels...")
    
    if call.data == "real_market":
        response = get_signal_for_asset("EURUSD=X", "EUR/USD (Real Market)")
    elif call.data == "crypto_market":
        response = get_signal_for_asset("BTC-USD", "BTC/USD (Crypto)")
    elif call.data == "otc_market":
        response = get_signal_for_asset("GBPUSD=X", "EUR/USD OTC (Quotex Style)")
    else:
        response = "Invalid selection."
        
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")
    markup.add(back_btn)
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=response,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    """Wapas main menu par jaane ke liye"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🌐 Real Market (EUR/USD, GBP/USD)", callback_data="real_market")
    btn2 = types.InlineKeyboardButton("🪙 Crypto Market (BTC/USD, ETH/USD)", callback_data="crypto_market")
    btn3 = types.InlineKeyboardButton("🔄 OTC Market (Quotex OTC Simulated)", callback_data="otc_market")
    markup.add(btn1, btn2, btn3)
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🤖 **Main Menu:** Market select karein:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Interactive Telegram Bot is up and running...")
    bot.infinity_polling()
