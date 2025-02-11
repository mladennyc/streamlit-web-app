import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -----------------------------
# Helper Functions
# -----------------------------

def calculate_dividend_growth(dividends):
    # Group by year and sum the dividends for each year
    annual_dividends = dividends.groupby(dividends.index.year).sum()
    # Calculate year-over-year growth in dividends as percentage change
    dividend_growth = annual_dividends.pct_change() * 100
    return dividend_growth

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

def calculate_annual_dividend_yield(data, dividends):
    data['Year'] = data.index.year
    annual_dividends = dividends.groupby(dividends.index.year).sum()
    annual_avg_price = data.groupby('Year')['Close'].mean()
    annual_yield = (annual_dividends / annual_avg_price) * 100
    return annual_yield

def fetch_and_process_data(tickers, start_date, index_names):
    stock_data = {}
    annual_yields = {}
    for i, ticker in enumerate(tickers):
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, auto_adjust=False, actions=False)
        dividends = stock.dividends.loc[start_date:]
        
        if data.empty:
            st.warning(f"No data available for {ticker}. Skipping...")
            continue
        
        data = calculate_adjusted_prices(data, dividends)
        annual_yield = calculate_annual_dividend_yield(data, dividends)
        stock_data[index_names[i]] = data  # Store data using the provided name
        annual_yields[index_names[i]] = annual_yield  # Store yield using the provided name
    return stock_data, annual_yields

# -----------------------------
# App Setup with Tabs
# -----------------------------

st.title("Stock and Index Analysis Tool")

# Create two tabs:
#   - Tab 1: Empty for now.
#   - Tab 2: Contains inputs and analysis.
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

with tab1:
    st.write("This tab is empty for now.")

with tab2:
    st.header("Input Options")
    
    # Input widgets on the tab level:
    num_stocks = st.slider("Number of stocks to compare:", 1, 5, 2)
    tickers = []
    index_names = []  # List to store names for display
    for i in range(num_stocks):
        ticker = st.text_input(f"Enter stock ticker #{i+1}:", "").upper()
        if ticker:
            tickers.append(ticker)
            index_names.append(ticker)
    
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
        index_names.append(selected_index)
    
    start_date = st.text_input("Enter the start date (YYYY-MM-DD):", "2020-01-01")
    
    analyze_button = st.button("Analyze")
    
    if analyze_button:
        if not tickers:
            st.error("Please enter at least one stock ticker or index.")
        else:
            with st.spinner("Fetching and analyzing data..."):
                stock_data, annual_yields = fetch_and_process_data(tickers, start_date, index_names)
            
            # Normalized Regular Price Comparison
            st.subheader("Normalized Regular Price Comparison")
            plt.figure(figsize=(10, 6))
            for name, data in stock_data.items():
                plt.plot(data.index, data['Normalized Regular Price'], label=name)
            plt.xlabel("Date")
            plt.ylabel("Value ($1 Start)")
            plt.legend()
            plt.grid()
            st.pyplot(plt)
            
            # Normalized Accumulated Value (Dividends Paid)
            st.subheader("Normalized Accumulated Value (Dividends Paid)")
            plt.figure(figsize=(10, 6))
            for name, data in stock_data.items():
                plt.plot(data.index, data['Normalized Dividends Paid'], label=name)
            plt.xlabel("Date")
            plt.ylabel("Value ($1 Start)")
            plt.legend()
            plt.grid()
            st.pyplot(plt)
            
            # Normalized Accumulated Value (Dividends Reinvested)
            st.subheader("Normalized Accumulated Value (Dividends Reinvested)")
            plt.figure(figsize=(10, 6))
            for name, data in stock_data.items():
                plt.plot(data.index, data['Normalized Dividends Reinvested'], label=name)
            plt.xlabel("Date")
            plt.ylabel("Value ($1 Start)")
            plt.legend()
            plt.grid()
            st.pyplot(plt)
            
            # Annual Dividend Yield Comparison
            st.subheader("Annual Dividend Yield Comparison")
            plt.figure(figsize=(10, 6))
            for name, annual_yield in annual_yields.items():
                if annual_yield is not None:
                    plt.plot(annual_yield.index, annual_yield, label=name, marker='o')
            plt.xlabel("Year")
            plt.ylabel("Dividend Yield (%)")
            plt.legend()
            plt.grid()
            st.pyplot(plt)
            
            # Final value summary table
            st.subheader("Final Value of $1 Invested")
            results = []
            for name, data in stock_data.items():
                final_row = data.iloc[-1]
                results.append({
                    "Ticker": name,
                    "Regular Price ($)": f"{final_row['Normalized Regular Price']:.2f}",
                    "Dividends Paid ($)": f"{final_row['Normalized Dividends Paid']:.2f}",
                    "Dividends Reinvested ($)": f"{final_row['Normalized Dividends Reinvested']:.2f}"
                })
            results_df = pd.DataFrame(results).set_index("Ticker")
            st.table(results_df)
