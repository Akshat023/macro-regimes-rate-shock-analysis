"""
Scenario Analysis Module
Rate shock stress testing using historical analogs
"""

import pandas as pd
import numpy as np

class RateShockAnalyzer:
    """Analyze +100bps rate shock scenarios"""
    
    def __init__(self, data, config):
        self.data = data.copy()
        self.config = config
        self.shock_dates = None
        self.shock_responses = None
        
    def identify_shocks(self):
        """
        Identify historical rate shock events
        Definition: 10Y yield increases by >70bps in one month
        """
        print("Identifying historical rate shocks...")
        
        df = self.data.copy()
        
        # Calculate yield changes over lookback period
        lookback = self.config.SHOCK_LOOKBACK
        df['YIELD_CHG'] = df['TREASURY_10Y'].diff(lookback)
        
        # Identify shocks
        threshold = self.config.SHOCK_YIELD_THRESHOLD
        shock_mask = df['YIELD_CHG'] > threshold
        shock_candidates = df[shock_mask].index.tolist()
        
        # Filter: minimum 6 months between shocks (avoid overlaps)
        filtered_shocks = []
        last_shock = None
        
        for date in shock_candidates:
            if last_shock is None or (date - last_shock).days > 180:
                filtered_shocks.append(date)
                last_shock = date
        
        self.shock_dates = filtered_shocks
        
        print(f"✓ Identified {len(filtered_shocks)} rate shock events:")
        for date in filtered_shocks:
            yield_at_shock = df.loc[date, 'TREASURY_10Y']
            yield_change = df.loc[date, 'YIELD_CHG']
            print(f"  {date.date()}: 10Y Yield = {yield_at_shock:.2f}% "
                  f"(+{yield_change:.2f}% over {lookback} days)")
        
        return filtered_shocks
    
    def measure_shock_response(self, shock_dates=None):
        """
        Calculate asset returns following each shock
        Horizon: 3 months forward from shock date
        """
        if shock_dates is None:
            if self.shock_dates is None:
                raise ValueError("Must run identify_shocks() first or provide shock_dates")
            shock_dates = self.shock_dates
        
        print(f"Measuring {self.config.SHOCK_HORIZON}-day forward returns...")
        
        df = self.data
        horizon = self.config.SHOCK_HORIZON
        responses = []
        
        for shock_date in shock_dates:
            try:
                shock_idx = df.index.get_loc(shock_date)
                
                # Skip if insufficient forward data
                if shock_idx + horizon >= len(df):
                    print(f"  ⚠ Skipping {shock_date.date()}: insufficient forward data")
                    continue
                
                # Calculate forward returns
                response = {
                    'shock_date': shock_date,
                    'start_yield': df['TREASURY_10Y'].iloc[shock_idx],
                    'end_yield': df['TREASURY_10Y'].iloc[shock_idx + horizon]
                }
                
                for ticker in self.config.TICKERS.keys():
                    if ticker not in df.columns:
                        continue
                    
                    start_price = df[ticker].iloc[shock_idx]
                    end_price = df[ticker].iloc[shock_idx + horizon]
                    ret = (end_price / start_price - 1) * 100
                    response[f'{ticker}_ret'] = ret
                
                responses.append(response)
                print(f"  ✓ {shock_date.date()}: Returns measured")
                
            except Exception as e:
                print(f"  ✗ Error processing {shock_date.date()}: {e}")
                continue
        
        self.shock_responses = pd.DataFrame(responses)
        
        if len(self.shock_responses) > 0:
            print(f"✓ Shock responses measured: {len(self.shock_responses)} events")
        else:
            print("⚠ No valid shock responses found")
        
        return self.shock_responses
    
    def portfolio_stress_test(self, weights=None, shock_responses=None):
        """
        Calculate portfolio impact distribution across scenarios
        Returns percentile-based summary
        """
        if shock_responses is None:
            if self.shock_responses is None or len(self.shock_responses) == 0:
                raise ValueError("No shock responses available. Run measure_shock_response() first")
            shock_responses = self.shock_responses
        
        if weights is None:
            weights = self.config.PORTFOLIO_WEIGHTS
        
        print("Running portfolio stress test...")
        
        # Calculate portfolio return for each shock event
        portfolio_rets = []
        
        for _, row in shock_responses.iterrows():
            port_ret = sum(
                weights.get(ticker, 0) * row.get(f'{ticker}_ret', 0)
                for ticker in weights.keys()
            )
            portfolio_rets.append(port_ret)
        
        portfolio_rets = np.array(portfolio_rets)
        
        # Calculate summary statistics
        summary = {
            'median': np.median(portfolio_rets),
            'p10': np.percentile(portfolio_rets, 10),   # Tail loss
            'p90': np.percentile(portfolio_rets, 90),   # Best case
            'mean': np.mean(portfolio_rets),
            'std': np.std(portfolio_rets),
            'min': np.min(portfolio_rets),
            'max': np.max(portfolio_rets),
            'count': len(portfolio_rets)
        }
        
        # Create detailed summary table
        detailed_rows = []
        
        for pct, label in [(10, 'Tail (10th pct)'), 
                           (50, 'Median'), 
                           (90, 'Best (90th pct)')]:
            row = {'Scenario': label}
            
            for ticker in self.config.TICKERS.keys():
                ret_col = f'{ticker}_ret'
                if ret_col in shock_responses.columns:
                    row[ticker] = np.percentile(shock_responses[ret_col], pct)
            
            row['Portfolio'] = np.percentile(portfolio_rets, pct)
            detailed_rows.append(row)
        
        detailed_table = pd.DataFrame(detailed_rows)
        
        print("✓ Portfolio stress test complete")
        print(f"\nPortfolio Impact Summary (3-Month Horizon):")
        print(f"  Median Loss:  {summary['median']:6.2f}%")
        print(f"  Tail Loss:    {summary['p10']:6.2f}%")
        print(f"  Best Case:    {summary['p90']:6.2f}%")
        print(f"  Sample Size:  {summary['count']} events")
        
        return summary, detailed_table
    
    def get_shock_data(self):
        """Return shock dates and responses"""
        return {
            'shock_dates': self.shock_dates,
            'shock_responses': self.shock_responses
        }