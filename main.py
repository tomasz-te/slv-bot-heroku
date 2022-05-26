import yfinance as yf
import pandas_ta as ta
import pandas as pd
import pickle
from flask import Flask, render_template

def get_slv_price():
    df = yf.Ticker("SLV")
    data = df.history()
    price = data['Close'].iloc[-1]
    return round(price,2)


# Preparing current input data for model
def generate_signal():
    df = yf.Ticker("SI=F")
    data = df.history(period="max")
    data.drop([column for column in data.columns if column not in ['Open','Close', 'High', 'Low']], axis=1, inplace=True)
    df = yf.Ticker("GC=F")
    gold = df.history(period="max")
    data['Gold'] = gold['Close']
    data['Gold'].fillna(method='ffill', inplace=True)
    windows = [10, 30, 100]

    for window in windows:
        data["Silver_"+str(window)] = data['Close'].rolling(window+1).apply(lambda x: (x.iloc[window] - x.iloc[0]) / x.iloc[0] * 100)
        data["Gold_"+str(window)] = data['Gold'].rolling(window+1).apply(lambda x: (x.iloc[window] - x.iloc[0]) / x.iloc[0] * 100)

    data['RSI_14']=ta.rsi(data['Close'],lenght=14)

    MACD = ta.macd(data['Close'],fast=12, slow=26, signal=9)
    data = pd.concat([data,MACD],axis=1)

    STOCH = ta.stoch(high=data.High,low=data.Low,close=data.Close)
    data = pd.concat([data, STOCH], axis=1)

    data.drop(['Open','High','Low','Close','Gold'], axis=1, inplace=True)

    model = pickle.load(open('model.sav', 'rb'))
    current_signal = int(model.predict(data.iloc[-1:])[0])
    print('Current signal: ', current_signal)
    if current_signal == 1:
        return 'BUY'
    else:
        return 'SELL/HOLD'

app = Flask(__name__)

@app.route('/')
def home():
    if generate_signal() == 'BUY':
        color = '33cccc'
    else:
        color = 'ff0000'
    return render_template('index.html', signal = generate_signal(), price = get_slv_price(), color = color)

if __name__ == '__main__':
    app.run(debug=True)
#
# print(get_slv_price())
# generate_signal()
