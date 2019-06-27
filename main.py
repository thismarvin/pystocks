import os
import sys
import re
import datetime
import json
import requests
from pytz import timezone
from twilio.rest import Client
from tkinter import Tk, Canvas

# region GUI Setup
master = Tk()
master.title("Stock Data GUI")
canvas_width = 320 * 2
canvas_height = 180 * 2
w = Canvas(master, width=canvas_width, height=canvas_height)
w.configure(background='black')
w.pack()
# endregion

# region Load Credentials
file = open("credentials.txt", "r")
# endregion

# region Twilio API Setup
enable_sms = False

if len(sys.argv) == 3:
    if str(sys.argv[2]).lower() == "true":
        enable_sms = True
    elif str(sys.argv[2]).lower() == "false":
        enable_sms = False

account_sid = file.readline().split(" ")[1].strip()
auth_token = file.readline().split(" ")[1].strip()
twilio_number = file.readline().split(" ")[1].strip()
your_number = file.readline().split(" ")[1].strip()
user_set_twilio_key = False if account_sid == "your_account_sid" else True

if enable_sms:
    if user_set_twilio_key:
        client = Client(account_sid, auth_token)
    else:
        print("Make sure to change the default Twilio keys located in the \"credentials.txt\" file")
# endregion

# region AlphaVantage API Setup
alpha_api_key = file.readline().split(" ")[1].strip()
file.close()

user_set_alpha_api_key = False if alpha_api_key == "your_alphavantage_api_key" else True
api_update_frequency = 60

if (not user_set_alpha_api_key):
    print("Make sure to change the default Alpha Vantage API key located in the \"credentials.txt\" file")
# endregion

# region Get Today's Date
date = datetime.datetime.now().strftime("%Y-%m-%d")
day_of_the_week = datetime.datetime(int(re.split(
    "-", date)[0]), int(re.split("-", date)[1]), int(re.split("-", date)[2])).weekday()
assert day_of_the_week <= 4, "The market is not open over the weekend!"
# endregion

# region Target Stock Setup
target_stock = "SPY" if len(sys.argv) == 1 else str(sys.argv[1]).upper()
target_profit = 0.001
maximum_loss = 0.001
short_ema_period = 12 * 5
long_ema_period = 26 * 5
multiplier = 1000000

if len(sys.argv) == 1:
    print("Your target stock was not defined; the program will default to using \"SPY\"")
    print("Refer to the README file on instructions to define a target stock and other prerequisites")
if len(target_stock) > 4 or re.search("\d", target_stock):
    print("The target stock you entered is not valid, defaulting to \"SPY\"")
# endregion

# region Initialize Lists
price_time = [None] * 390
prices = [None] * 390
volume = [None] * 390
vwap_time = [None] * 390
vwap = [None] * 390
short_ema_time = [None] * 390
short_ema = [None] * 390
long_ema_time = [None] * 390
long_ema = [None] * 390
macd = [None] * int(390 / 5)
macd_signal = [None] * int(390 / 5)
macd_histogram = [None] * int(390 / 5)
macd_time = [None] * int(390 / 5)
rsi = [None] * int(390 / 5)
rsi_time = [None] * int(390 / 5)

derivative_long_ema = [None] * 390
derivative_macd = [None] * 390
derivative_macd_signal = [None] * 390

transactions = []
# endregion

# region Initialize Chart variables
buffer = canvas_width * 0.05
chart_height = (canvas_height - buffer * 2) / 2
# endregion


def smallest(list):
    minimum = None
    for i in range(len(list)):
        if list[i] != None:
            minimum = list[i]
            break
    for i in range(0, len(list)):
        if list[i] != None and list[i] < minimum:
            minimum = list[i]
    return minimum


def largest(list):
    largest = None
    for i in range(len(list)):
        if list[i] != None:
            largest = list[i]
            break
    for i in range(0, len(list)):
        if list[i] != None and list[i] > largest:
            largest = list[i]
    return largest


def time_index(time):
    hour = int(time[:2])
    minute = int(time[3:5])
    return((hour - 9) * 60 + minute - 30 - 1)


def last_entry():
    for i in range(len(prices) - 1, -1, -1):
        if prices[i] != None:
            return i
    return 0


def send_sms(action_time, text):
    "Sends SMS via Twilio API"
    if enable_sms:
        action_hour = int(action_time[0:2])
        action_minute = int(action_time[3:5])
        action_minutes = action_hour * 60 + action_minute

        time_zone = timezone('US/Eastern')
        current_hour = int(datetime.datetime.now(time_zone).strftime("%H"))
        current_minute = int(datetime.datetime.now(time_zone).strftime("%M"))
        current_minutes = current_hour * 60 + current_minute

        if (action_minutes + 5 >= current_minutes):
            client.messages.create(
                body=text,
                to=your_number,
                from_=twilio_number
            )


def load_pricing():
    # Load Pricing Data from AlphaVantage API
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={}&interval=1min&outputsize=full&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text

    try:
        json_object = json.loads(data)

        # Parse Pricing Data from API
        for category in json_object:
            if category == "Time Series (1min)":
                for time in json_object[category]:
                    if (time[:10] == date and time[11:16] not in price_time):
                        prices[time_index(time[11:16])] = int(
                            float(json_object[category][time]["4. close"]) * multiplier)
                        price_time[time_index(time[11:16])] = time[11:16]
                        volume[time_index(time[11:16])] = int(
                            json_object[category][time]["5. volume"])
    except:
        print("Unable to load pricing data.")


def load_VWAP():
    # Load VWAP Data from API
    url = "https://www.alphavantage.co/query?function=VWAP&symbol={}&interval=1min&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text

    try:
        json_object = json.loads(data)

        # Parse VWAP Data from API
        for category in json_object:
            if category == "Technical Analysis: VWAP":
                for time in json_object[category]:
                    if (time[:10] == date and time[11:16] not in vwap_time):
                        if float(json_object[category][time]["VWAP"]) != 0:
                            vwap[time_index(time[11:16])] = int(
                                float(json_object[category][time]["VWAP"]) * multiplier)
                            vwap_time[time_index(time[11:16])] = time[11:16]
    except:
        print("Unable to load VWAP data.")


def load_EMAs():
    # Load Short EMA Data from API
    url = "https://www.alphavantage.co/query?function=EMA&symbol={}&interval=1min&time_period={}&series_type=close&apikey={}".format(
        target_stock, short_ema_period, alpha_api_key)
    data = requests.get(url).text

    try:
        json_object = json.loads(data)

        # Parse Short EMA Data from API
        for category in json_object:
            if category == "Technical Analysis: EMA":
                for time in json_object[category]:
                    if (time[:10] == date and time[11:16] not in short_ema_time):
                        short_ema[time_index(time[11:16])] = int(
                            float(json_object[category][time]["EMA"]) * multiplier)
                        short_ema_time[time_index(time[11:16])] = time[11:16]
    except:
        print("Unable to load Short EMA data.")

    # Load Long EMA Data from API
    url = "https://www.alphavantage.co/query?function=EMA&symbol={}&interval=1min&time_period={}&series_type=close&apikey={}".format(
        target_stock, long_ema_period, alpha_api_key)
    data = requests.get(url).text

    try:
        json_object = json.loads(data)

        # Parse Long EMA Data from API
        for category in json_object:
            if category == "Technical Analysis: EMA":
                for time in json_object[category]:
                    if (time[:10] == date and time[11:16] not in long_ema_time):
                        long_ema[time_index(time[11:16])] = int(
                            float(json_object[category][time]["EMA"]) * multiplier)
                        long_ema_time[time_index(time[11:16])] = time[11:16]
    except:
        print("Unable to load Long EMA data.")


def load_MACD():
    # Load MACD Data from API
    url = "https://www.alphavantage.co/query?function=MACD&symbol={}&interval=5min&series_type=close&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text

    try:
        json_object = json.loads(data)

        # Parse MACD Data from API
        for category in json_object:
            if category == "Technical Analysis: MACD":
                for time in json_object[category]:
                    if (time[:10] == date and time[11:] not in macd_time):
                        macd[int(time_index(time[11:16]) / 5)
                             ] = int(float(json_object[category][time]["MACD"]) * multiplier)
                        macd_signal[int(time_index(time[11:16]) / 5)] = int(
                            float(json_object[category][time]["MACD_Signal"]) * multiplier)
                        macd_histogram[int(time_index(time[11:16]) / 5)] = int(
                            float(json_object[category][time]["MACD_Hist"]) * multiplier)
                        macd_time[int(time_index(time[11:16]) / 5)] = time[11:]
    except:
        print("Unable to load MACD data.")


def load_RSI():
    # Load RSI Data from API
    url = "https://www.alphavantage.co/query?function=RSI&symbol={}&interval=5min&time_period=10&series_type=close&apikey={}".format(
        target_stock, alpha_api_key)
    data = requests.get(url).text

    try:
        json_object = json.loads(data)

        # Parse Pricing Data from API
        for category in json_object:
            if category == "Technical Analysis: RSI":
                for time in json_object[category]:
                    if (time[:10] == date and time[11:] not in rsi_time):
                        rsi[int(time_index(time[11:16]) / 5)
                            ] = int(float(json_object[category][time]["RSI"]) * multiplier)
                        rsi_time[int(time_index(time[11:16]) / 5)] = time[11:]
    except:
        print("Unable to load RSI data.")


def data_load_correctly():
    if prices.count(None) == 390:
        print("Error loading data from the Alpha Vantage API")
        return False
    else:
        return True


def update_derivatives():
    for i in range(1, len(long_ema)):
        if long_ema[i] != None and long_ema[i - 1] != None:
            derivative_long_ema[i] = long_ema[i] - long_ema[i - 1]

    for i in range(1, len(macd)):
        if macd[i] != None and macd[i - 1] != None:
            derivative_macd[i] = macd[i] - macd[i - 1]

    for i in range(1, len(macd_signal)):
        if macd_signal[i] != None and macd_signal[i - 1] != None:
            derivative_macd_signal[i] = macd_signal[i] - macd_signal[i - 1]


def update_bot():
    "Update the all powerful Trading AI Bot"
    for i in range(0, last_entry()):
        if (
            prices[i] != None and
            long_ema[i] != None and
            short_ema != None and
            macd[int((i + 1) / 5) - 1] != None and
            macd_signal[int((i + 1) / 5) - 1] != None and
            rsi[int((i + 1) / 5) - 1] != None and
            derivative_long_ema[i] != None and
            derivative_macd[int((i + 1) / 5) - 1] != None and
            derivative_macd_signal[int((i + 1) / 5) - 1] != None
        ):
            if (
                len(transactions) % 2 == 0 and
                i not in transactions and
                (i > transactions[-1] if len(transactions) > 0 else True) and
                i >= 59 and
                i < 389 - 30 and
                prices[i] < vwap[i] and
                (i >= 4 and macd[int((i + 1) / 5) - 1] < macd_signal[int((i + 1) / 5) - 1]) and
                float(derivative_long_ema[i] / multiplier) > -0.05 and
                float(derivative_macd[int((i + 1) / 5) - 1] / multiplier) >= 0.002 and
                float(derivative_macd_signal[int((i + 1) / 5) - 1] / multiplier) > -0.05 and
                float(rsi[int((i + 1) / 5) - 1] / multiplier) <= 60
            ):
                action = ("Buy at {} EST for ${}").format(
                    price_time[i][:5], float(prices[i] / multiplier))
                print(action)
                send_sms(price_time[i][:5], action)
                transactions.append(i)
            elif (
                len(transactions) % 2 != 0 and
                i not in transactions and
                (i > transactions[-1] if len(transactions) > 0 else True) and
                (
                    i >= 389 - 5 or
                    prices[i] >= prices[transactions[-1]] * (1 + target_profit) or
                    prices[i] <= prices[transactions[-1]] * (1 - maximum_loss) or
                    (
                        float(derivative_long_ema[i] / multiplier) <= -0.05 and
                        float(derivative_macd[int((i + 1) / 5) - 1] / multiplier) <= -0.05 and
                        float(derivative_macd_signal[int(
                            (i + 1) / 5) - 1] / multiplier) <= -0.05
                    )
                )
            ):
                action = ("Sell at {} EST for ${}").format(
                    price_time[i][:5], float(prices[i] / multiplier))
                print(action)
                send_sms(price_time[i][:5], action)
                transactions.append(i)


def update_title():
    master.title("{} ${} {} EST".format(target_stock, float(
        prices[last_entry()] / multiplier), price_time[last_entry()]))


def save_todays_data():
    file = open("data/" + date + ".csv", "w")
    str = "minute,closing_price,volume,vwap,short_ema,long_ema,macd,macd_signal,rsi\n"
    file.write(str)
    for i in range(0, len(prices)):
        str = ("{},{},{},{},{},{},{},{},{}\n").format(
            i + 1,
            float(prices[i] / multiplier) if prices[i] != None else "???",
            volume[i] if volume[i] != None and volume[i] != 0 else "???",
            float(
                vwap[i] / multiplier) if vwap[i] != None and vwap[i] != 0 else "???",
            float(short_ema[i] /
                  multiplier) if short_ema[i] != None else "???",
            float(long_ema[i] / multiplier) if long_ema[i] != None else "???",
            "???" if macd[int((i + 1) / 5) - 1] == None else (
                float((macd[int((i + 1) / 5) - 1]) / multiplier) if i > 3 else 0),
            "???" if macd_signal[int((i + 1) / 5) - 1] == None else (
                float((macd_signal[int((i + 1) / 5) - 1]) / multiplier) if i > 3 else 0),
            "???" if rsi[int((i + 1) / 5) - 1] == None else float(rsi[int((i + 1) / 5) - 1] / multiplier) if i > 3 else 0)
        file.write(str)
    file.close()


def volume_scaled(value):
    maxs = []
    sum = 0
    for i in range(0, len(volume)):
        if volume[i] != None:
            sum += volume[i]
        if i > 0 and i % 5 == 0:
            maxs.append(sum)
            sum = 0
    max = largest(maxs)
    return canvas_height - (value * chart_height * 0.5 / max) - chart_height - buffer


def draw_volume():
    x_scale = (canvas_width - buffer * 2) / (390)
    sum = 0
    for i in range(0, len(volume)):
        if volume[i] != None:
            sum += volume[i]
        if i > 0 and i % 5 == 0:
            w.create_rectangle((i) * x_scale + buffer, volume_scaled(0),
                               (i - 5) * x_scale + buffer, volume_scaled(sum), fill="#232323")
            sum = 0


def pricing_scaled(price):
    mins = [smallest(prices), smallest(short_ema),
            smallest(long_ema), smallest(vwap)]
    maxs = [largest(prices), largest(short_ema),
            largest(long_ema), largest(vwap)]
    range = largest(maxs) - smallest(mins)
    min = smallest(mins)
    return canvas_height - ((price - min) * chart_height / range) - chart_height - buffer


def draw_pricing():
    x_scale = (canvas_width - buffer * 2) / 390

    # Draw VWAP Data
    for i in range(1, last_entry()):
        if vwap[i] != None and vwap[i - 1] != None:
            w.create_line((i - 1) * x_scale + buffer, pricing_scaled(vwap[i - 1]), (
                i) * x_scale + buffer, pricing_scaled(vwap[i]), fill="#FFFFFF", width=1)

    # Draw Pricing Data
    for i in range(1, last_entry()):
        if prices[i] != None and prices[i - 1] != None:
            color = "#00E756" if prices[last_entry(
            )] > prices[0] else "#FF004D"
            w.create_line((i - 1) * x_scale + buffer, pricing_scaled(
                prices[i - 1]), (i) * x_scale + buffer, pricing_scaled(prices[i]), fill=color, width=2)

    # Draw Short EMA Data
    for i in range(1, last_entry()):
        if short_ema[i] != None and short_ema[i - 1] != None:
            w.create_line((i - 1) * x_scale + buffer, pricing_scaled(short_ema[i - 1]), (
                i) * x_scale + buffer, pricing_scaled(short_ema[i]), fill="#FF77A8", width=2)

    # Draw Long EMA Data
    for i in range(1, last_entry()):
        if long_ema[i] != None and long_ema[i - 1] != None:
            w.create_line((i - 1) * x_scale + buffer, pricing_scaled(long_ema[i - 1]), (
                i) * x_scale + buffer, pricing_scaled(long_ema[i]), fill="#FFA300", width=2)


def macd_scaled(value):
    mins = [smallest(macd), smallest(macd_signal), smallest(macd_histogram), 0]
    min = abs(smallest(mins))
    maxs = [largest(macd), largest(macd_signal), largest(macd_histogram)]
    max = abs(largest(maxs))
    range = max + min
    value += min
    return canvas_height - (value * chart_height * 0.6 / range) - chart_height * 0.4 - buffer


def draw_MACD():
    x_scale = (canvas_width - buffer * 2) / (390 / 5)
    # Draw MACD Data
    for i in range(0, len(macd) - 1):
        if macd[i] != None and macd[i + 1] != None and macd_signal[i] != None and macd_signal[i + 1] != None:
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


def rsi_scaled(value):
    min = smallest(rsi) if smallest(rsi) < 30 * multiplier else 30 * multiplier
    max = largest(rsi) if largest(rsi) > 80 * multiplier else 80 * multiplier
    range = max - min
    return canvas_height - ((value - min) * chart_height * 0.35 / range) - buffer


def draw_RSI():
    x_scale = (canvas_width - buffer * 2) / (390 / 5)

    # Draw RSI Oversold and Undersold Lines
    w.create_line(buffer, rsi_scaled(70 * multiplier), canvas_width - buffer,
                  rsi_scaled(70 * multiplier), fill="#FFFFFF", width=1)
    w.create_line(buffer, rsi_scaled(30 * multiplier), canvas_width - buffer,
                  rsi_scaled(30 * multiplier), fill="#FFFFFF", width=1)

    # Draw MACD Data
    for i in range(0, len(rsi) - 1):
        if rsi[i] != None and rsi[i + 1]:
            w.create_line((i + 1) * x_scale + buffer, rsi_scaled(
                rsi[i]), (i + 2) * x_scale + buffer, rsi_scaled(rsi[i + 1]), fill="#FFFFFF", width=3)


def draw_transactions():
    "Draw lines at buy and sell signals"
    x_scale = (canvas_width - buffer * 2) / 390
    for i in range(0, len(transactions)):
        if i % 2 == 0:
            w.create_line(transactions[i] * x_scale + buffer, buffer, transactions[i]
                          * x_scale + buffer, canvas_height - buffer, fill="#6888FC", width=2)
        else:
            w.create_line(transactions[i] * x_scale + buffer, buffer, transactions[i]
                          * x_scale + buffer, canvas_height - buffer, fill="#D800CC", width=2)


def update():
    # Update with new data
    if user_set_alpha_api_key:
        load_pricing()
        load_VWAP()
        load_EMAs()
        load_MACD()
        load_RSI()

    if data_load_correctly():
        update_derivatives()
        update_bot()
        update_title()
        # Clear and redraw data
        w.delete("all")
        draw_volume()
        draw_pricing()
        draw_MACD()
        draw_RSI()
        draw_transactions()

        save_todays_data()

    if last_entry() < 390 - 1:
        master.after(1000 * api_update_frequency, update)


# Update Chart
update()

# Start GUI
master.mainloop()
