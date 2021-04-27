import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import json
import base64
import cufflinks as cf
import yfinance as yf
import datetime

st.set_page_config(layout="wide")
st.sidebar.title('Options')
option = st.sidebar.selectbox("Select Dashboard", ('S&P 500 Companies',  'Crypto', 'Stocktwits', 'Stock'), 3)
st.header(option)

#Function to load Companies data
@st.cache
def load_data_C():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    html = pd.read_html(url, header = 0)
    df = html[0]
    return df

# Download S&P500 data
@st.cache
def filedownload_C(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="SP500.csv">Download CSV File</a>'
    return href

# Plot Closing Price of Query Symbol
@st.cache(suppress_st_warning=True)
def price_plot(symbol):
    df = pd.DataFrame(data[symbol].Close)
    df['Date'] = df.index
    plt.fill_between(df.Date, df.Close, color='skyblue', alpha=0.3)
    plt.plot(df.Date, df.Close, color='skyblue', alpha=0.8)
    plt.xticks(rotation=90)
    plt.title(symbol, fontweight='bold')
    plt.xlabel('Date', fontweight='bold')
    plt.ylabel('Closing Price', fontweight='bold')
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

#Function to load Crypto data
@st.cache
def load_data():
    cmc = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')

    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coins = {}
    coin_data = json.loads(data.contents[0])
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    for i in listings:
        coins[str(i['id'])] = i['slug']

    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:
        coin_name.append(i['slug'])
        coin_symbol.append(i['symbol'])
        price.append(i['quote'][currency_price_unit]['price'])
        percent_change_1h.append(i['quote'][currency_price_unit]['percentChange1h']) # percent_change_1h
        percent_change_24h.append(i['quote'][currency_price_unit]['percentChange24h']) #percent_change_24h
        percent_change_7d.append(i['quote'][currency_price_unit]['percentChange7d']) # percent_change_7d
        market_cap.append(i['quote'][currency_price_unit]['marketCap']) # market_cap
        volume_24h.append(i['quote'][currency_price_unit]['volume24h']) # volume_24h

    df = pd.DataFrame(columns=['coin_name', 'coin_symbol', 'marketCap', 'percentChange1h', 'percentChange24h', 'percentChange7d', 'price', 'volume24h'])
    df['coin_name'] = coin_name
    df['coin_symbol'] = coin_symbol
    df['price'] = price
    df['percentChange1h'] = percent_change_1h
    df['percentChange24h'] = percent_change_24h
    df['percentChange7d'] = percent_change_7d
    df['marketCap'] = market_cap
    df['volume24h'] = volume_24h
    return df

# Download CSV data for Crypto
@st.cache
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

# When Stockwits tab is selected
if option == 'S&P 500 Companies':
    df = load_data_C()
    sector = df.groupby('GICS Sector')
    # Sidebar - Sector selection
    sorted_sector_unique = sorted( df['GICS Sector'].unique() )
    selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, sorted_sector_unique)
    # Filtering data
    df_selected_sector = df[ (df['GICS Sector'].isin(selected_sector)) ]

    st.header('Display Companies in Selected Sector')
    st.write('Data Dimension: ' + str(df_selected_sector.shape[0]) + ' rows and ' + str(df_selected_sector.shape[1]) + ' columns.')
    st.dataframe(df_selected_sector)
    st.markdown(filedownload_C(df_selected_sector), unsafe_allow_html=True)
    data = yf.download(
        tickers = list(df_selected_sector[:10].Symbol),
        period = "ytd",
        interval = "1d",
        group_by = 'ticker',
        auto_adjust = True,
        prepost = True,
        threads = True,
        proxy = None
    )
    num_company = st.sidebar.slider('Number of Companies', 1, 5)
    if st.button('Show Plots'):
        st.header('Stock Closing Price')
        for i in list(df_selected_sector.Symbol)[:num_company]:
            price_plot(i)


# When Stockwits tab is selected
if option == 'Stocktwits':
    symbol = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5)
    r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json")
    data = r.json()
    try:
        for message in data['messages']:
            st.image(message['user']['avatar_url'])
            st.write(message['user']['username'])
            st.write(message['created_at'])
            st.write(message['body'])
    except:
        st.write("Symbol not Valid!")


# When Crypto tab is selected
if option == 'Crypto':
    st.title('Crypto Price DashBoard')
    col1 = st.sidebar
    col2, col3 = st.beta_columns((2,1))

    #---------------------------------#
    # Sidebar + Main panel
    col1.header('Input Options')

    ## Sidebar - Currency price unit
    currency_price_unit = col1.selectbox('Currency for price', ['USD'])
    df = load_data()
    ## Sidebar - Cryptocurrency selections
    sorted_coin = sorted( df['coin_symbol'] )
    selected_coin = col1.multiselect('Cryptocurrency', sorted_coin, sorted_coin)

    df_selected_coin = df[ (df['coin_symbol'].isin(selected_coin)) ] # Filtering data

    ## Sidebar - Number of coins to display
    num_coin = col1.slider('Display Top N Coins', 1, 100, 100)
    df_coins = df_selected_coin[:num_coin]

    ## Sidebar - Percent change timeframe
    percent_timeframe = col1.selectbox('Percent change time frame',
                                       ['7d','24h', '1h'])
    percent_dict = {"7d":'percentChange7d',"24h":'percentChange24h',"1h":'percentChange1h'}
    selected_percent_timeframe = percent_dict[percent_timeframe]

    ## Sidebar - Sorting values
    sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])

    col2.subheader('Price Data of Selected Cryptocurrency')
    col2.write('Data Dimension: ' + str(df_selected_coin.shape[0]) + ' rows and ' + str(df_selected_coin.shape[1]) + ' columns.')

    col2.dataframe(df_coins)

    col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

    #---------------------------------#
    # Preparing data for Bar plot of % Price change
    col2.subheader('Table of % Price Change')
    df_change = pd.concat([df_coins.coin_symbol, df_coins.percentChange1h, df_coins.percentChange24h, df_coins.percentChange7d], axis=1)
    df_change = df_change.set_index('coin_symbol')
    df_change['positive_percent_change_1h'] = df_change['percentChange1h'] > 0
    df_change['positive_percent_change_24h'] = df_change['percentChange24h'] > 0
    df_change['positive_percent_change_7d'] = df_change['percentChange7d'] > 0
    col2.dataframe(df_change)

    # Conditional creation of Bar plot (time frame)
    col3.subheader('Bar plot of % Price Change')

    if percent_timeframe == '7d':
        if sort_values == 'Yes':
            df_change = df_change.sort_values(by=['percentChange7d'])
        col3.write('*7 days period*')
        plt.figure(figsize=(5,25))
        plt.subplots_adjust(top = 1, bottom = 0)
        df_change['percentChange7d'].plot(kind='barh', color=df_change.positive_percent_change_7d.map({True: 'g', False: 'r'}))
        col3.pyplot(plt)
    elif percent_timeframe == '24h':
        if sort_values == 'Yes':
            df_change = df_change.sort_values(by=['percentChange24h'])
        col3.write('*24 hour period*')
        plt.figure(figsize=(5,25))
        plt.subplots_adjust(top = 1, bottom = 0)
        df_change['percentChange24h'].plot(kind='barh', color=df_change.positive_percent_change_24h.map({True: 'g', False: 'r'}))
        col3.pyplot(plt)
    else:
        if sort_values == 'Yes':
            df_change = df_change.sort_values(by=['percentChange1h'])
        col3.write('*1 hour period*')
        plt.figure(figsize=(5,25))
        plt.subplots_adjust(top = 1, bottom = 0)
        df_change['percentChange1h'].plot(kind='barh', color=df_change.positive_percent_change_1h.map({True: 'g', False: 'r'}))
        col3.pyplot(plt)

if option == 'Stock':
    # Sidebar
    st.sidebar.subheader('Query parameters')
    start_date = st.sidebar.date_input("Start date", datetime.date(2019, 1, 1))
    end_date = st.sidebar.date_input("End date", datetime.date(2021, 4, 23))

    # Retrieving tickers data
    ticker_list = pd.read_csv('https://raw.githubusercontent.com/dataprofessor/s-and-p-500-companies/master/data/constituents_symbols.txt')
    tickerSymbol = st.sidebar.selectbox('Stock ticker', ticker_list) # Select ticker symbol
    tickerData = yf.Ticker(tickerSymbol) # Get ticker data
    tickerDf = tickerData.history(period='1d', start=start_date, end=end_date) #get the historical prices for this ticker

    # Ticker information
    string_logo = '<img src=%s>' % tickerData.info['logo_url']
    st.markdown(string_logo, unsafe_allow_html=True)

    string_name = tickerData.info['longName']
    st.header('**%s**' % string_name)

    string_summary = tickerData.info['longBusinessSummary']
    st.info(string_summary)

    # Ticker data
    st.header('**Ticker data**')
    st.write(tickerDf)

    # Bollinger bands
    st.header('**Bollinger Bands**')
    qf=cf.QuantFig(tickerDf,title='First Quant Figure',legend='top',name='GS')
    qf.add_bollinger_bands()
    fig = qf.iplot(asFigure=True)
    st.plotly_chart(fig)


