import time
import telebot
import yfinance as yf
import pandas as pd

# Aapke credentials direct configured hain
TOKEN = "8959002705:AAHeJRhXkBCQl_hIYd0ehD4BVYURZCNsyHg"
CHAT_ID = "1375185299"

bot = telebot.TeleBot(TOKEN)

# Aap yahan apna pasandida asset symbol dal sakte hain (jaise BTC-USD, EURUSD=X)
SYMBOL = "BTC-USD"  
INTERVAL = "1h"
PERIOD = "5d"

def fetch_data():
    """Market data download karne ke liye function"""
    try:
        df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, progress=False)
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def find_support_resistance(df, window=5):
    """Rolling window ka use karke Support aur Resistance levels nikalna"""
    df['Support'] = df['Low'].rolling(window=window, center=True).min()
    df['Resistance'] = df['High'].rolling(window=window, center=True).max()
    
    try:
        support_level = df['Support'].dropna().iloc[-1]
        resistance_level = df['Resistance'].dropna().iloc[-1]
        return float(support_level), float(resistance_level)
    except Exception:
        return None, None

def check_market_and_send():
    print("Checking market levels...")
    df = fetch_data()
    if df is None or df.empty:
        return

    current_price = float(df['Close'].iloc[-1])
    support, resistance = find_support_resistance(df)

    if support is None or resistance is None:
        return

    print(f"Price: {current_price} | Support: {support:.2f} | Resistance: {resistance:.2f}")

    message = ""
    # Agar price Support ya Resistance ke 0.3% ke andar hai, toh signal generate karein
    if abs(current_price - support) / current_price < 0.003:
        message = (f"🟢 *BUY / CALL SIGNAL*\n\n"
                   f"📊 Asset: `{SYMBOL}`\n"
                   f"💰 Current Price: `{current_price:.2f}`\n"
                   f"🛡️ Support Level: `{support:.2f}`\n"
                   f"✨ Status: Price is testing Support zone!")
                   
    elif abs(current_price - resistance) / current_price < 0.003:
        message = (f"🔴 *SELL / PUT SIGNAL*\n\n"
                   f"📊 Asset: `{SYMBOL}`\n"
                   f"💰 Current Price: `{current_price:.2f}`\n"
                   f"⚡ Resistance Level: `{resistance:.2f}`\n"
                   f"✨ Status: Price is testing Resistance zone!")

    # Agar signal mila hai, toh message bhej do
    if message:
        try:
            bot.send_message(CHAT_ID, message, parse_mode="Markdown")
            print("Signal successfully sent to Telegram!")
        except Exception as e:
            print(f"Failed to send telegram message: {e}")

if __name__ == "__main__":
    print("Trading bot started and running as background worker...")
    
    try:
        bot.send_message(CHAT_ID, "🚀 S&R Trading Bot successfully live ho gaya hai!")
    except Exception as e:
        print(f"Startup message error: {e}")

    # Render background worker ke liye continuous loop
    while True:
        check_market_and_send()
        # Har 15 minutes (900 seconds) me market dobara check karega
        time.sleep(900)
