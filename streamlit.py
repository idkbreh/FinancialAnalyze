import yfinance as yf
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

sns.set_style("whitegrid")

st.title("Financial Analysis Dashboard")
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a section", ["Recession Probability", "Stock Analysis", "Profit Prediction"])

if page == "Recession Probability":
    st.header("Economic Recession Probability Analysis")
    
    url = "https://www.investing.com/economic-calendar/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"id": "economicCalendarData"})

    rows = []
    for tr in table.tbody.find_all("tr"):
        row = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        rows.append(row)

    df = pd.DataFrame(rows)
    date_row = df.iloc[0, 0]
    df = df.drop(index=0)
    df.columns = ["Time", "Cur.", "Imp.", "Event", "Actual", "Forecast", "Previous", "Extra"]
    df = df.drop(columns=["Extra"])
    df['Time'] = df['Time'].ffill()
    df['Cur.'] = df['Cur.'].ffill()

    def convert_to_thai_time(time_str):
        try:
            gmt_minus_4_time = datetime.strptime(time_str, '%H:%M')
            thai_time = gmt_minus_4_time + timedelta(hours=11)
            return thai_time.strftime('%H:%M')
        except ValueError:
            return time_str

    df['Time'] = df['Time'].apply(convert_to_thai_time)
    recession_signals = df[(df['Actual'] < df['Forecast']) | (df['Actual'] < df['Previous'])].shape[0]
    total_events = df.shape[0]
    recession_probability = (recession_signals / total_events) * 100

    st.write(f"Recession Probability: **{recession_probability:.2f}%**")
    st.write(f"Date: **{date_row}**")
    
    st.write("Cleaned DataFrame:")
    st.dataframe(df.head(20))
    
    fig, ax = plt.subplots()
    ax.pie([recession_probability, 100 - recession_probability], labels=['Recession Signals', 'Other'], autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff'])
    ax.axis('equal')
    st.pyplot(fig)

elif page == "Stock Analysis":
    st.header("Stock Analysis: Worth Buying Score")
    
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'FB', 'NFLX', 'NVDA', 'BRK-B', 'JPM', 'V', 'MA', 'UNH', 'HD', 'PG', 'DIS', 'PYPL', 'INTC', 'CSCO', 'PFE']
    selected_stocks = st.multiselect("Select stocks to analyze", stocks)
    search_stock = st.text_input("Search for a specific stock by ticker symbol (e.g., 'GOOG', 'BABA')")

    if search_stock:
        if search_stock.upper() not in selected_stocks:
            selected_stocks.append(search_stock.upper())
            st.write(f"Added {search_stock.upper()} to your selection.")

    data = []

    thresholds = {
        'P/E Ratio': {'min': 10, 'max': 35},
        'P/B Ratio': {'min': 1, 'max': 10},
        'Dividend Yield': {'min': 0.5, 'max': 5},
        'EPS Growth': {'min': 5, 'max': 30},
        'Debt-to-Equity': {'min': 0, 'max': 1},
        'ROE': {'min': 10, 'max': 30}
    }

    def normalize(value, min_val, max_val):
        if value is None:
            return 0
        if value < min_val:
            return 0
        elif value > max_val:
            return 100
        else:
            return ((value - min_val) / (max_val - min_val)) * 100

    for stock in selected_stocks:
        stock_info = yf.Ticker(stock).info
        
        pe_ratio = stock_info.get('trailingPE', None)
        pb_ratio = stock_info.get('priceToBook', None)
        dividend_yield = stock_info.get('dividendYield', 0) * 100
        eps_growth = stock_info.get('earningsQuarterlyGrowth', 0) * 100
        debt_to_equity = stock_info.get('debtToEquity', None)
        roe = stock_info.get('returnOnEquity', None)
        
        pe_score = normalize(pe_ratio, thresholds['P/E Ratio']['min'], thresholds['P/E Ratio']['max'])
        pb_score = normalize(pb_ratio, thresholds['P/B Ratio']['min'], thresholds['P/B Ratio']['max'])
        dividend_yield_score = normalize(dividend_yield, thresholds['Dividend Yield']['min'], thresholds['Dividend Yield']['max'])
        eps_growth_score = normalize(eps_growth, thresholds['EPS Growth']['min'], thresholds['EPS Growth']['max'])
        debt_to_equity_score = normalize(debt_to_equity, thresholds['Debt-to-Equity']['min'], thresholds['Debt-to-Equity']['max'])
        roe_score = normalize(roe, thresholds['ROE']['min'], thresholds['ROE']['max'])
        
        weights = {
            'P/E': 0.2,
            'P/B': 0.2,
            'Dividend Yield': 0.15,
            'EPS Growth': 0.25,
            'Debt-to-Equity': 0.1,
            'ROE': 0.1
        }
        
        worth_buying_score = (weights['P/E'] * pe_score +
                              weights['P/B'] * pb_score +
                              weights['Dividend Yield'] * dividend_yield_score +
                              weights['EPS Growth'] * eps_growth_score +
                              weights['Debt-to-Equity'] * debt_to_equity_score +
                              weights['ROE'] * roe_score)
        
        data.append([stock, pe_ratio, pb_ratio, dividend_yield, eps_growth, debt_to_equity, roe, worth_buying_score])

    df = pd.DataFrame(data, columns=['Stock', 'P/E Ratio', 'P/B Ratio', 'Dividend Yield', 'EPS Growth', 'Debt-to-Equity', 'ROE', 'Worth Buying (%)'])

    st.write("Stock Analysis DataFrame:")
    st.dataframe(df)
    
    fig = px.bar(df, x='Stock', y='Worth Buying (%)', title='Worth Buying Score by Stock', color='Worth Buying (%)', color_continuous_scale=px.colors.sequential.Viridis)
    st.plotly_chart(fig)

elif page == "Profit Prediction":
    st.header("Predict Your Investment Profit")
    
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'FB', 'NFLX', 'NVDA', 'BRK-B', 'JPM', 'V', 'MA', 'UNH', 'HD', 'PG', 'DIS', 'PYPL', 'INTC', 'CSCO', 'PFE']
    selected_stocks = st.multiselect("Select stocks", stocks)
    search_stock = st.text_input("Search for a specific stock by ticker symbol (e.g., 'GOOG', 'BABA')")

    if search_stock:
        if search_stock.upper() not in selected_stocks:
            selected_stocks.append(search_stock.upper())
            st.write(f"Added {search_stock.upper()} to your selection.")

    investment_amount = st.number_input("Enter your investment amount (in Baht)", min_value=0.0, step=100.0, value=10000.0)
    investment_duration = st.number_input("Enter the investment duration (in months)", min_value=1, step=1, value=12)
    
    if investment_duration <= 1:
        period = '1mo'
    elif investment_duration <= 3:
        period = '3mo'
    elif investment_duration <= 6:
        period = '6mo'
    elif investment_duration <= 12:
        period = '1y'
    elif investment_duration <= 24:
        period = '2y'
    elif investment_duration <= 60:
        period = '5y'
    else:
        period = '10y'

    if selected_stocks and investment_amount > 0:
        total_profit = 0
        data = []
        for stock in selected_stocks:
            ticker = yf.Ticker(stock)
            current_price = ticker.history(period='1d').iloc[-1]['Close']
            history_data = ticker.history(period=period)
            
            if len(history_data) < investment_duration:
                st.warning(f"Not enough data for {stock} to predict profit over {investment_duration} months.")
                continue

            past_price = history_data.iloc[0]['Close']
            future_price = history_data.iloc[-1]['Close']
            return_percentage = (future_price - past_price) / past_price

            projected_future_price = current_price * (1 + return_percentage)

            profit = investment_amount * (projected_future_price - current_price) / current_price
            total_profit += profit
            data.append([stock, current_price, projected_future_price, return_percentage * 100, profit])
        
        if data:
            df = pd.DataFrame(data, columns=['Stock', 'Current Price', 'Projected Future Price', 'Return (%)', 'Profit (Baht)'])
            st.write("Prediction Results:")
            st.dataframe(df)
            
            fig = px.bar(df, x='Stock', y='Profit (Baht)', title='Predicted Profit by Stock', color='Profit (Baht)', color_continuous_scale=px.colors.sequential.Viridis)
            st.plotly_chart(fig)

            if total_profit > 0:
                st.success(f"Total Expected Profit: **{total_profit:.2f} Baht**")
            else:
                st.error(f"Total Expected Loss: **{abs(total_profit):.2f} Baht**")
