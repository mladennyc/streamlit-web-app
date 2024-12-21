import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Function to calculate adjusted prices and normalize
def calculate_adjusted_prices(data, dividends):
    dividends = dividends.reindex(data.index).fillna(0)

    # Regular Price
    data['Regular Price'] = data['Close']

    # Dividends Paid: Cumulative dividends added to price
    data['Dividends'] = dividends
    data['Cumulative Dividends'] = data['Dividends'].cumsum()
    data['Dividends Paid'] = data['Close'] + data['Cumulative Dividends']

    # Dividends Reinvested: Calculate reinvested value over time
    data['Shares Held'] = 1.0
    for i in range(1, len(data)):
        previous_shares = data['Shares Held'].iloc[i - 1]
        current_dividend = data['Dividends'].iloc[i] * previous_shares
        current_price = data['Close'].iloc[i]
        additional_shares = current_dividend / current_price if current_dividend > 0 else 0
        data.loc[data.index[i], 'Shares Held'] = previous_shares + additional_shares
    data['Dividends Reinvested'] = data['Shares Held'] * data['Close']

    # Normalize all values to start at $1
    for col in ['Regular Price', 'Dividends Paid', 'Dividends Reinvested']:
        data[f'Normalized {col}'] = data[col] / data[col].iloc[0]

    return data

# Function to calculate annual dividend yield
def calculate_annual_dividend_yield(data, dividends):
    data['Year'] = data.index.year
    annual_dividends = dividends.groupby(dividends.index.year).sum()
    annual_avg_price = data.groupby('Year')['Close'].mean()
    annual_yield = (annual_dividends / annual_avg_price) * 100
    return annual_yield

# Function to fetch and process data
def fetch_and_process_data(tickers, start_date, index_names):
    stock_data = {}
    annual_yields = {}
    for i, ticker in enumerate(tickers):
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date)
        dividends = stock.dividends.loc[start_date:]

        if data.empty:
            st.warning(f"No data available for {ticker}. Skipping...")
            continue

        data = calculate_adjusted_prices(data, dividends)
        annual_yield = calculate_annual_dividend_yield(data, dividends)
        stock_data[index_names[i]] = data  # Store data using the index name
        annual_yields[index_names[i]] = annual_yield  # Store yield using index name
    return stock_data, annual_yields

# Streamlit app setup
st.title("Stock and Index Analysis Tool")

# Sidebar for inputs
with st.sidebar:
    st.header("Input Options")
    num_stocks = st.slider("Number of stocks to compare:", 1, 5, 2)

    tickers = []
    index_names = []  # List to store index names
    for i in range(num_stocks):
        ticker = st.text_input(f"Enter stock ticker #{i+1}:", "").upper()
        if ticker:
            tickers.append(ticker)
            index_names.append(ticker)  # Store the ticker name here for now

    include_indices = st.checkbox("Include a major index")
    if include_indices:
        index_options = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "Nasdaq 100": "^NDX",
            "Russell 2000": "^RUT",
            "FTSE 100": "^FTSE"
        }
        selected_index = st.selectbox("Select an index to include:", list(index_options.keys()))
        tickers.append(index_options[selected_index])
        index_names.append(selected_index)  # Store the selected index name

    start_date = st.text_input("Enter the start date (YYYY-MM-DD):", "2020-01-01")

    analyze_button = st.button("Analyze")

# Fetch and process data
if analyze_button:
    if not tickers:
        st.error("Please enter at least one stock ticker or index.")
    else:
        with st.spinner("Fetching and analyzing data..."):
            stock_data, annual_yields = fetch_and_process_data(tickers, start_date, index_names)

        # Main content area
        st.subheader("Normalized Regular Price Comparison")
        plt.figure(figsize=(10, 6))
        for ticker, data in stock_data.items():
            plt.plot(data.index, data['Normalized Regular Price'], label=ticker)
        plt.xlabel("Date")
        plt.ylabel("Value ($1 Start)")
        plt.legend()
        plt.grid()
        st.pyplot(plt)

        st.subheader("Normalized Accumulated Value (Dividends Paid)")
        plt.figure(figsize=(10, 6))
        for ticker, data in stock_data.items():
            plt.plot(data.index, data['Normalized Dividends Paid'], label=ticker)
        plt.xlabel("Date")
        plt.ylabel("Value ($1 Start)")
        plt.legend()
        plt.grid()
        st.pyplot(plt)

        st.subheader("Normalized Accumulated Value (Dividends Reinvested)")
        plt.figure(figsize=(10, 6))
        for ticker, data in stock_data.items():
            plt.plot(data.index, data['Normalized Dividends Reinvested'], label=ticker)
        plt.xlabel("Date")
        plt.ylabel("Value ($1 Start)")
        plt.legend()
        plt.grid()
        st.pyplot(plt)

        st.subheader("Annual Dividend Yield Comparison")
        plt.figure(figsize=(10, 6))
        for ticker, annual_yield in annual_yields.items():
            if annual_yield is not None:
                plt.plot(annual_yield.index, annual_yield, label=ticker, marker='o')
        plt.xlabel("Year")
        plt.ylabel("Dividend Yield (%)")
        plt.legend()
        plt.grid()
        st.pyplot(plt)

        # Final value summary table
        st.subheader("Final Value of $1 Invested")
        results = []
        for ticker, data in stock_data.items():
            final_row = data.iloc[-1]
            results.append({
                "Ticker": ticker,
                "Regular Price ($)": f"{final_row['Normalized Regular Price']:.2f}",
                "Dividends Paid ($)": f"{final_row['Normalized Dividends Paid']:.2f}",
                "Dividends Reinvested ($)": f"{final_row['Normalized Dividends Reinvested']:.2f}"
            })
        results_df = pd.DataFrame(results).set_index("Ticker")
        st.table(results_df)
