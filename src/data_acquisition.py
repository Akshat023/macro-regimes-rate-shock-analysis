"""
Data Acquisition Module
Fetches macro and market data from FRED and Yahoo Finance
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataAcquisition:
    """Fetch and combine macro and market data"""
    
    def __init__(self, start_date, end_date, fred_api_key=None):
        self.start_date = start_date
        self.end_date = end_date
        self.fred_api_key = fred_api_key
        
    def fetch_fred_data(self):
        """
        Fetch Federal Reserve Economic Data
        
        For production: Install fredapi and use real data
        pip install fredapi
        from fredapi import Fred
        fred = Fred(api_key=self.fred_api_key)
        fed_funds = fred.get_series('DFF', start_date, end_date)
        
        For demo: Generate realistic simulated data
        """
        print("Fetching FRED data (Fed Funds, 10Y Treasury)...")
        
        if self.fred_api_key and self.fred_api_key.strip():
            try:
                from fredapi import Fred
                fred = Fred(api_key=self.fred_api_key)
                
                fed_funds = fred.get_series('DFF', 
                                           observation_start=self.start_date,
                                           observation_end=self.end_date)
                treasury_10y = fred.get_series('DGS10',
                                              observation_start=self.start_date,
                                              observation_end=self.end_date)
                
                df = pd.DataFrame({
                    'FED_FUNDS': fed_funds,
                    'TREASURY_10Y': treasury_10y
                })
                
                print("✓ Real FRED data fetched successfully")
                return df
                
            except Exception as e:
                print(f"⚠ FRED API error: {e}. Using simulated data.")
                return self._generate_simulated_data()
        else:
            print("⚠ No FRED API key provided. Using simulated data.")
            print("   Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
            return self._generate_simulated_data()
    
    def _generate_simulated_data(self):
        """Generate realistic simulated macro data"""
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        
        # Simulate Fed Funds Rate based on historical patterns
        fed_funds = pd.Series(index=dates, dtype=float)
        
        for date in dates:
            year = date.year
            month = date.month
            
            # Historical pattern simulation
            if year <= 2003:
                base = 2.5
            elif year <= 2006:
                base = 1.0 + (year - 2003) * 1.2
            elif year <= 2008:
                base = 5.0 - (year - 2006) * 0.5
            elif year <= 2015:
                base = 0.25
            elif year <= 2019:
                base = 0.25 + (year - 2015) * 0.5
            elif year <= 2021:
                base = 0.10
            else:
                base = 0.10 + (year - 2021) * 1.8 + (month / 12) * 0.3
            
            fed_funds[date] = max(0, base + np.random.normal(0, 0.15))
        
        # 10Y yield typically trades 150-200bps above Fed Funds
        treasury_10y = fed_funds + 1.5 + np.random.normal(0, 0.4, len(dates))
        treasury_10y = pd.Series(treasury_10y, index=dates).clip(lower=0.5)
        
        return pd.DataFrame({
            'FED_FUNDS': fed_funds,
            'TREASURY_10Y': treasury_10y
        })
    
    def fetch_market_data(self, tickers):
        """Fetch equity, bond, and volatility data from Yahoo Finance"""
        print(f"Fetching market data for {', '.join(tickers.keys())}...")
        
        ticker_list = list(tickers.keys()) + ['^VIX']
        
        try:
            raw = yf.download(ticker_list, 
                             start=self.start_date, 
                             end=self.end_date,
                             progress=False,
                             auto_adjust=False)
            
            # Handle multi-column format
            if isinstance(raw.columns, pd.MultiIndex):
                data = raw.xs('Adj Close', axis=1, level=0)
            else:
                data = raw[['Adj Close']]
                data.columns = ticker_list
            # Rename VIX
            if '^VIX' in data.columns:
                data = data.rename(columns={'^VIX': 'VIX'})
            
            # Validate all tickers present
            missing = set(ticker_list) - set(data.columns)
            if missing:
                print(f"⚠ Missing tickers: {missing}")
            
            print(f"✓ Market data fetched: {len(data)} days")
            return data
            
        except Exception as e:
            print(f"✗ Error fetching market data: {e}")
            raise
    
    def combine_data(self, fred_data, market_data):
        """Merge macro and market data on date index"""
        print("Combining datasets...")
        
        # Align on date index (inner join)
        combined = market_data.join(fred_data, how='inner')
        
        # Forward fill missing values (weekends, holidays)
        combined = combined.fillna(method='ffill')
        
        # Drop any remaining NaNs
        initial_rows = len(combined)
        combined = combined.dropna()
        dropped = initial_rows - len(combined)
        
        if dropped > 0:
            print(f"⚠ Dropped {dropped} rows with missing data")
        
        print(f"✓ Combined dataset: {len(combined)} days, {len(combined.columns)} variables")
        
        return combined
    
    def save_data(self, data, filename='combined_data.csv'):
        """Save processed data to CSV"""
        filepath = f"data/processed/{filename}"
        data.to_csv(filepath)
        print(f"✓ Data saved to {filepath}")