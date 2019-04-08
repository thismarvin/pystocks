import os
import sys
import datetime
import requests
import json
import numpy as np

from twilio.rest import Client
from tkinter import *

# Load Credentials
file = open("credentials.txt", "r")

# Twilio API Setup
disable_sms = True

account_sid = file.readline().split(" ")[1].strip()
auth_token = file.readline().split(" ")[1].strip()
twilio_number = file.readline().split(" ")[1].strip()
your_number = file.readline().split(" ")[1].strip()
user_set_twilio_key = False if account_sid == "your_account_sid" else True

if not disable_sms:
    if user_set_twilio_key:
        client = Client(account_sid, auth_token)
    else:
        print("Make sure to change the default Twilio keys located in the \"credentials.txt\" file")

# Alpha API Setup
alpha_api_key = file.readline().split(" ")[1].strip()
file.close()

user_set_alpha_api_key = False if alpha_api_key == "your_alphavantage_api_key" else True
api_update_frequency = 60

if (not user_set_alpha_api_key):
    print("Make sure to change the default Alpha Vantage API key located in the \"credentials.txt\" file")


# Target Stock Setup
if len(sys.argv) == 1:
    print("Your target stock was not defined; the program will default to using \"SPY\"")
    print("Refer to the README file on instructions to define a target stock and other prerequisites")
target_stock = "SPY" if len(sys.argv) == 1 else sys.argv[1]
multiplier = 1000000
short_ema_period = 60
long_ema_period = 120

# GUI Setup
master = Tk()
master.title("Advanced Stock Trading AI 3000")
canvas_width = 320 * 2
canvas_height = 180 * 2
w = Canvas(master, width=canvas_width, height=canvas_height)
w.configure(background='black')
w.pack()

# Get Today's Date
date = datetime.datetime.now().strftime("%Y-%m-%d")

# Initialize Lists
price_time = []
prices = []
short_ema_time = []
short_ema = []
long_ema_time = []
long_ema = []
macd = []
macd_signal = []
macd_histogram = []
macd_time = []
rsi = []
rsi_time = []

derivative_long_ema = [0]
derivative_macd = [0]
derivative_macd_signal = [0]

transactions = []

# Initialize Chart variables
buffer = canvas_width * 0.05
chart_height = (canvas_height - buffer * 2) / 2


# Helper Methods
def smallest(list):
    min = list[0]
    for i in range(0, len(list)):
        if list[i] < min:
            min = list[i]
    return min


def largest(list):
    max = list[0]
    for i in range(0, len(list)):
        if list[i] > max:
            max = list[i]
    return max


# Sends SMS via Twilio API
def send_sms(text):
    if not disable_sms:
        client.messages.create(
            body=text,
            to=your_number,
            from_=twilio_number
        )


# Methods for Alpha API Calls
def load_pricing(new_data):
    # Load Pricing Data from API
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={}&interval=1min&outputsize=full&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text
    json_object = json.loads(data)

    # Parse Pricing Data from API
    for category in json_object:
        if category == "Time Series (1min)":
            for time in json_object[category]:
                if (time[:10] == date and time[11:16] not in price_time):
                    if not new_data:
                        prices.insert(
                            0, int(float(json_object[category][time]["4. close"]) * multiplier))
                        price_time.insert(0, time[11:16])
                    else:
                        prices.append(
                            int(float(json_object[category][time]["4. close"]) * multiplier))
                        price_time.append(time[11:16])

    # Load Short EMA Data from API
    url = "https://www.alphavantage.co/query?function=EMA&symbol={}&interval=1min&time_period={}&series_type=close&apikey={}".format(
        target_stock, short_ema_period, alpha_api_key)
    data = requests.get(url).text
    json_object = json.loads(data)

    # Parse Short EMA Data from API
    for category in json_object:
        if category == "Technical Analysis: EMA":
            for time in json_object[category]:
                if (time[:10] == date and time[11:16] not in short_ema_time):
                    if not new_data:
                        short_ema.insert(
                            0, int(float(json_object[category][time]["EMA"]) * multiplier))
                        short_ema_time.insert(0, time[11:16])
                    else:
                        short_ema.append(
                            int(float(json_object[category][time]["EMA"]) * multiplier))
                        short_ema_time.append(time[11:16])

    # Load Long EMA Data from API
    url = "https://www.alphavantage.co/query?function=EMA&symbol={}&interval=1min&time_period={}&series_type=close&apikey={}".format(
        target_stock, long_ema_period, alpha_api_key)
    data = requests.get(url).text
    json_object = json.loads(data)

    # Parse Long EMA Data from API
    for category in json_object:
        if category == "Technical Analysis: EMA":
            for time in json_object[category]:
                if (time[:10] == date and time[11:16] not in long_ema_time):
                    if not new_data:
                        long_ema.insert(
                            0, int(float(json_object[category][time]["EMA"]) * multiplier))
                        long_ema_time.insert(0, time[11:16])
                    else:
                        long_ema.append(
                            int(float(json_object[category][time]["EMA"]) * multiplier))
                        long_ema_time.append(time[11:16])


def load_MACD(new_data):
    # Load MACD Data from API
    url = "https://www.alphavantage.co/query?function=MACD&symbol={}&interval=5min&series_type=close&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text
    json_object = json.loads(data)

    # Parse MACD Data from API
    for category in json_object:
        if category == "Technical Analysis: MACD":
            for time in json_object[category]:
                if (time[:10] == date and time[11:] not in macd_time):
                    if not new_data:
                        macd.insert(
                            0, int(float(json_object[category][time]["MACD"]) * multiplier))
                        macd_signal.insert(
                            0, int(float(json_object[category][time]["MACD_Signal"]) * multiplier))
                        macd_histogram.insert(
                            0, int(float(json_object[category][time]["MACD_Hist"])*multiplier))
                        macd_time.insert(0, time[11:])
                    else:
                        macd.append(
                            int(float(json_object[category][time]["MACD"])*multiplier))
                        macd_signal.append(
                            int(float(json_object[category][time]["MACD_Signal"])*multiplier))
                        macd_histogram.append(
                            int(float(json_object[category][time]["MACD_Hist"])*multiplier))
                        macd_time.append(time[11:])


def load_RSI(new_data):
    # Load RSI Data from API
    url = "https://www.alphavantage.co/query?function=RSI&symbol={}&interval=5min&time_period=10&series_type=close&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text
    json_object = json.loads(data)

    # Parse Pricing Data from API
    for category in json_object:
        if category == "Technical Analysis: RSI":
            for time in json_object[category]:
                if (time[:10] == date and time[11:] not in rsi_time):
                    if not new_data:
                        rsi.insert(
                            0, int(float(json_object[category][time]["RSI"]) * multiplier))
                        rsi_time.insert(0, time[11:])
                    else:
                        rsi.append(
                            int(float(json_object[category][time]["RSI"]) * multiplier))
                        rsi_time.append(time[11:])


def data_load_correctly():
    if len(prices) == 0 or len(short_ema) == 0 or len(long_ema) == 0 or len(macd) == 0 or len(macd_signal) == 0 or len(macd_histogram) == 0 or len(rsi) == 0:
        print("Error loading data from the Alpha Vantage API")
        return False
    else:
        return True


# Calculate Derivatives
def update_derivatives():
    # Long EMA Derivative
    for i in range(len(derivative_long_ema), len(long_ema)):
        if i > 0:
            derivative_long_ema.append(int(long_ema[i] - long_ema[i - 1]))
    # MACD Derivative
    for i in range(len(derivative_macd), len(macd)):
        if i > 0:
            derivative_macd.append(int(macd[i] - macd[i - 1]))
    # MACD Signal Derivative
    for i in range(len(derivative_macd_signal), len(macd_signal)):
        if i > 0:
            derivative_macd_signal.append(
                int(macd_signal[i] - macd_signal[i - 1]))


# Update the all powerful Trading AI Bot
def update_bot():
    for i in range(0, len(prices)):
        if (
            len(transactions) % 2 == 0 and
            i not in transactions and
            (i > transactions[-1] if len(transactions) > 0 else True) and
            i > 60 and
            i < 390 - 30 and
            float(derivative_long_ema[i] / multiplier) > -0.05 and
            float(derivative_macd[int(i / 5) - 1] / multiplier) > 0 and
            float(derivative_macd_signal[int(i / 5) - 1] / multiplier) > 0 and
            float(macd_histogram[int(i / 5) - 1] / multiplier) >= 0.025 and
            float(rsi[int(i / 5) - 1] / multiplier) <= 60
        ):
            action = ("Buy at {} EST for ${}").format(
                price_time[i][:5], float(prices[i]) / multiplier)
            print(action)
            send_sms(action)
            transactions.append(i)
        elif (
            len(transactions) % 2 != 0 and
            i not in transactions and
            (i > transactions[-1] if len(transactions) > 0 else True) and
            (
                i >= 389 or
                (
                    macd[int(i / 5) - 1] < macd_signal[int(i / 5) - 1] and
                    float(derivative_macd[int(i / 5) - 1] / multiplier) < 0 and
                    float(derivative_macd_signal[int(
                        i / 5) - 1] / multiplier) < 0
                )
            )
        ):
            action = ("Sell at {} EST for ${}").format(
                price_time[i][:5], float(prices[i]) / multiplier)
            print(action)
            send_sms(action)
            transactions.append(i)


# Scale Y Pricing Values
def pricing_scaled(price):
    mins = [smallest(prices), smallest(short_ema), smallest(long_ema)]
    maxs = [largest(prices), largest(short_ema), largest(long_ema)]
    range = largest(maxs) - smallest(mins)
    min = smallest(mins)
    return canvas_height - ((price - min) * chart_height / range) - chart_height - buffer


def draw_pricing():
    x_scale = (canvas_width - buffer * 2) / 390
    # Draw Pricing Data
    for i in range(1, len(prices)):
        color = "#00E756" if prices[-1] > prices[0] else "#FF004D"
        w.create_line((i - 1) * x_scale + buffer, pricing_scaled(
            prices[i - 1]), (i) * x_scale + buffer, pricing_scaled(prices[i]), fill=color, width=2)

    # Draw Short EMA Data
    for i in range(1, len(short_ema)):
        w.create_line((i - 1) * x_scale + buffer, pricing_scaled(short_ema[i - 1]), (
            i) * x_scale + buffer, pricing_scaled(short_ema[i]), fill="#FF77A8", width=2)

    # Draw Long EMA Data
    for i in range(1, len(long_ema)):
        w.create_line((i - 1) * x_scale + buffer, pricing_scaled(long_ema[i - 1]), (
            i) * x_scale + buffer, pricing_scaled(long_ema[i]), fill="#FFA300", width=2)


# Scale MACD Values
def macd_scaled(value):
    range = largest(macd) + abs(smallest(macd))
    value += abs(smallest(macd))
    return canvas_height - (value * chart_height / 2 / range) - chart_height / 2 - buffer


def draw_MACD():
    x_scale = (canvas_width - buffer * 2) / (390 / 5)
    # Draw MACD Data
    for i in range(0, len(macd) - 1):
        color = "#00E756" if macd_scaled(macd[i]) < macd_scaled(
            macd_signal[i]) else "#FF004D"
        w.create_rectangle((i + 1) * x_scale + buffer, macd_scaled(0), (i + 2) * x_scale + buffer,
                           macd_scaled(0) + (macd_scaled(macd[i]) - macd_scaled(macd_signal[i])), fill=color)
        w.create_line((i + 1) * x_scale + buffer, macd_scaled(
            macd[i]), (i + 2) * x_scale + buffer, macd_scaled(macd[i + 1]), fill="#29ADFF", width=3)
        w.create_line((i + 1) * x_scale + buffer, macd_scaled(macd_signal[i]), (
            i + 2) * x_scale + buffer, macd_scaled(macd_signal[i + 1]), fill="#0000FC", width=3)

    # Draw MACD X Axis
    w.create_line(buffer, macd_scaled(0), canvas_width - buffer,
                  macd_scaled(0), fill="#FFFFFF", width=1)


# Scale RSI Values
def rsi_scaled(value):
    range = largest(rsi) - smallest(rsi)
    min = smallest(rsi) if smallest(rsi) < 30 * multiplier else 30 * multiplier
    return canvas_height - ((value - min) * chart_height * 0.4 / range) - buffer


def draw_RSI():
    x_scale = (canvas_width - buffer * 2) / (390 / 5)

    # Draw RSI Oversold and Undersold Lines
    w.create_line(buffer, rsi_scaled(70 * multiplier), canvas_width - buffer,
                  rsi_scaled(70 * multiplier), fill="#FFFFFF", width=1)
    w.create_line(buffer, rsi_scaled(30 * multiplier), canvas_width - buffer,
                  rsi_scaled(30 * multiplier), fill="#FFFFFF", width=1)

    # Draw MACD Data
    for i in range(0, len(rsi) - 1):
        w.create_line((i + 1) * x_scale + buffer, rsi_scaled(
            rsi[i]), (i + 2) * x_scale + buffer, rsi_scaled(rsi[i + 1]), fill="#FFFFFF", width=3)


# Draw lines at buy and sell signals
def draw_transactions():
    x_scale = (canvas_width - buffer * 2) / 390
    for i in range(0, len(transactions)):
        if i % 2 == 0:
            w.create_line(transactions[i] * x_scale + buffer, buffer, transactions[i]
                          * x_scale + buffer, canvas_height - buffer, fill="#6888FC", width=2)
        else:
            w.create_line(transactions[i] * x_scale + buffer, buffer, transactions[i]
                          * x_scale + buffer, canvas_height - buffer, fill="#D800CC", width=2)


def initialize():
    # Initialize with pre-existing data
    if user_set_alpha_api_key:
        load_pricing(False)
        load_MACD(False)
        load_RSI(False)

    if data_load_correctly():
        update_derivatives()
        update_bot()
        # Draw Data
        draw_pricing()
        draw_MACD()
        draw_RSI()
        draw_transactions()


def update():
    # Update with new data
    if user_set_alpha_api_key:
        load_pricing(True)
        load_MACD(True)
        load_RSI(True)

    if data_load_correctly():
        update_derivatives()
        update_bot()
        # Clear and redraw data
        w.delete("all")
        draw_pricing()
        draw_MACD()
        draw_RSI()
        draw_transactions()

    master.after(1000 * api_update_frequency, update)


# Initialize Chart
initialize()

# Update Chart
master.after(1000 * api_update_frequency, update)

# Start GUI
master.mainloop()
