# pystocks
a simple stock trading strategy and its respective visualization made using python

![Image of Program](https://github.com/thismarvin/pystocks/blob/master/Preview.png)

## Features
The program uses realtime stock data provided by [Alpha Vantage](https://www.alphavantage.co/) to suggest entry and exit points for potential stock trades. A visualization of the target stock's pricing and various technical indicators is rendered to a simple GUI made using python's tkinter. Optionally, the program can be linked to a [Twilio Account](https://www.twilio.com/), and any suggest trades can be sent directly to your phone via SMS.

## Initial Setup
Before taking advantage of the strategy, make sure to fill the `credentials.txt` file with your API keys. [Alpha Vantage](https://www.alphavantage.co/) provides a free API key, but the key is limited to 5 API calls per min and 500 API per day. Make sure to tweak the frequency at which the API is called to fit your needs by modifying the `api_update_frequency` variable (By default the API is called 5 times every minute). SMS Alerts are disabled by default, but they can be enabled after setting up a free [Twilio Account](https://www.twilio.com/) and entering the required information from your account.

## Running the Program
The program takes in two command line arguments. The first argument `Stock_Symbol` is your target stock, and the second argument `Enable_SMS_Alerts` is a boolean to toggle SMS Alerts from your [Twilio Account](https://www.twilio.com/)

`python main.py Stock_Symbol Enable_SMS_Alerts`

## Requirements
- requests
- twilio

## Strategy
The strategy mainly revolves around the MACD indicator, but also takes advantage of the RSI indicator and a long EMA. 

A buy signal is detected when the MACD value is less than the MACD Signal, the MACD value is increasing, and the MACD Signal appears to be starting to increase. Once a buy signal is detected it will be confirmed if the long EMA appears to be starting to increase and the RSI indicator is less than 60. A sell signal is detected if your target profit is reached, your maximum loss risk is reached, or when the MACD value, the MACD Signal, and the long EMA are decreasing. 

By default the strategy will suggest a buy signal between 10:30 AM EST and 3:30 PM EST. A sell signal will be suggested at any time as long as a buy signal exists prior. This is a day trading strategy, so a sell signal will be suggested at close if a buy signal has not been closed yet.

**Only invest as much money as you are willing to lose**. Technical Analysis is not always right. In fact, tweaking this strategy is encouraged!