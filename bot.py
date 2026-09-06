import time
from datetime import datetime, timedelta
import pytz
import telebot
import yfinance as yf
import pandas as pd

# Telegram Credentials
TOKEN = "8959002705:AAHeJRhXkBCQl_hIYd0ehD4BVYURZCNsyHg"
CHAT_ID = "1375185299"

bot = telebot.TeleBot(TOKEN)

# Quotex ke popular pairs (Yahoo Finance format: EURUSD=X, GBPUSD=X)
PAIRS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X"]
INTERVAL = "1m"
PERIOD = "1d"

def fetch_data(symbol):
    """Market data download karne ke liye function"""
    try:
        df = yf.download(symbol, period=PERIOD, interval=INTERVAL, progress=False)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def find_support_resistance(df, window=5):
    """Support aur Resistance levels calculate karna"""
    df['Support'] = df['Low'].rolling(window=window, center=True).min()
    df['Resistance'] = df['High'].rolling(window=window, center=True).max()
    
    try:
        support_level = df['Support'].dropna().iloc[-1]
        resistance_level = df['Resistance'].dropna().iloc[-1]
        return float(support_level), float(resistance_level)
    except Exception:
        return None, None

def check_market_and_send():
    print("Scanning Quotex markets for 1-min signals...")
    
    # India Standard Time (IST) zone setup
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist)
    
    open_time_str = current_time_ist.strftime("%H:%M:%S")
    # 1 minute expiry time
    expiry_time_str = (current_time_ist + timedelta(minutes=1)).strftime("%H:%M:%S")

    for symbol in PAIRS:
        df = fetch_data(symbol)
        if df is None or df.empty or len(df) < 10:
            continue

        current_price = float(df['Close'].iloc[-1])
        support, resistance = find_support_resistance(df)

        if support is None or resistance is None:
            continue

        # Clean symbol name for display (e.g., EURUSD=X -> EUR/USD)
        display_pair = symbol.replace("=X", "").replace("-", "/")

        message = ""
        # Support ke paas -> CALL (UP) Signal
        if abs(current_price - support) / current_price < 0.0008:
            message = (f"🎯 *QUOTEX 1-MIN SIGNAL* 🎯\n\n"
                       f"📊 Pair: `{display_pair}`\n"
                       f"📈 Direction: 🟢 **CALL (UP)**\n"
                       f"⏰ Open Time: `{open_time_str} IST`\n"
                       f"⏳ Expiry Time: `{expiry_time_str} IST` (1 Min)\n"
                       f"💰 Entry Price: `{current_price:.5f}`\n"
                       f"🛡️ Support Level: `{support:.5f}`")
                       
        # Resistance ke paas -> PUT (DOWN) Signal
        elif abs(current_price - resistance) / current_price < 0.0008:
            message = (f"🎯 *QUOTEX 1-MIN SIGNAL* 🎯\n\n"
                       f"📊 Pair: `{display_pair}`\n"
                       f"📉 Direction: 🔴 **PUT (DOWN)**\n"
                       f"⏰ Open Time: `{open_time_str} IST`\n"
                       f"⏳ Expiry Time: `{expiry_time_str} IST` (1 Min)\n"
                       f"💰 Entry Price: `{current_price:.5f}`\n"
                       f"⚡ Resistance Level: `{resistance:.5f}`")

        # Agar signal generate hua hai, toh Telegram par bhej do
        if message:
            try:
                bot.send_message(CHAT_ID, message, parse_mode="Markdown")
                print(f"Signal sent for {display_pair}!")
            except Exception as e:
                print(f"Failed to send telegram message: {e}")
            
            # Ek baar me ek hi signal bhejne ke liye break kar sakte hain ya saare check kar sakte hain
            break

if __name__ == "__main__":
    print("Quotex 1-Min S&R Bot started...")
    
    try:
        bot.send_message(CHAT_ID, "🚀 Quotex 1-Min Signal Bot live ho gaya hai!")
    except Exception as e:
        print(f"Startup message error: {e}")

    # Render background worker ke liye continuous loop (har 60 seconds me check karega)
    while True:
        check_market_and_send()
        time.sleep(60)
