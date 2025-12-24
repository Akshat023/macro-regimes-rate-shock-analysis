"""
Performance Analysis Module
Calculate returns, volatility, correlations by regime
"""

import pandas as pd
import numpy as np

class PerformanceAnalyzer:
    """Analyze asset performance across regimes"""
    
    def __init__(self, data, config):
        self.data = data.copy()
        self.config = config
        self.returns_data = None
        
    def calculate_returns(self):
        """Calculate daily returns for all assets"""
        print("Calculating asset returns...")
        
        df = self.data.copy()
        
        for ticker in self.config.TICKERS.keys():
            if ticker in df.columns:
                df[f'{ticker}_RET'] = df[ticker].pct_change()
        
        self.returns_data = df
        print(f"✓ Returns calculated for {len(self.config.TICKERS)} assets")
        
        return df
    
    def regime_performance(self):
        """Calculate comprehensive performance metrics by regime"""
        if self.returns_data is None:
            raise ValueError("Must run calculate_returns() first")
        
        print("Analyzing performance by regime...")
        
        df = self.returns_data
        results = []
        
        regimes = ['TIGHTENING', 'EASING', 'STRESS', 'NORMAL']
        
        for regime in regimes:
            regime_data = df[df['REGIME'] == regime]
            
            if len(regime_data) < 10:
                continue
            
            for ticker in self.config.TICKERS.keys():
                ret_col = f'{ticker}_RET'
                
                if ret_col not in df.columns:
                    continue
                
                returns = regime_data[ret_col].dropna()
                
                if len(returns) < 5:
                    continue
                
                # Annualized metrics
                ann_factor = self.config.ANNUALIZATION_FACTOR
                ann_return = returns.mean() * ann_factor * 100
                ann_vol = returns.std() * np.sqrt(ann_factor) * 100
                sharpe = ann_return / ann_vol if ann_vol > 0 else 0
                
                # Max drawdown
                cum_ret = (1 + returns).cumprod()
                running_max = cum_ret.expanding().max()
                drawdown = (cum_ret - running_max) / running_max
                max_dd = drawdown.min() * 100
                
                # Win rate
                win_rate = (returns > 0).sum() / len(returns) * 100
                
                results.append({
                    'Regime': regime,
                    'Asset': ticker,
                    'Ann_Return_pct': round(ann_return, 2),
                    'Ann_Vol_pct': round(ann_vol, 2),
                    'Sharpe': round(sharpe, 2),
                    'Max_DD_pct': round(max_dd, 2),
                    'Win_Rate_pct': round(win_rate, 1),
                    'Observations': len(returns)
                })
        
        performance_df = pd.DataFrame(results)
        print(f"✓ Performance metrics calculated for {len(performance_df)} regime-asset pairs")
        
        return performance_df
    
    def rolling_correlation(self, asset1='SPY', asset2='TLT', window=None):
        """Calculate rolling correlation between two assets"""
        if self.returns_data is None:
            raise ValueError("Must run calculate_returns() first")
        
        if window is None:
            window = self.config.ROLLING_CORR_WINDOW
        
        print(f"Calculating {window}-day rolling correlation: {asset1} vs {asset2}...")
        
        df = self.returns_data.copy()
        
        ret1_col = f'{asset1}_RET'
        ret2_col = f'{asset2}_RET'
        
        if ret1_col not in df.columns or ret2_col not in df.columns:
            raise ValueError(f"Return columns not found for {asset1} or {asset2}")
        
        # Calculate rolling correlation
        corr_col = f'{asset1}_{asset2}_CORR'
        df[corr_col] = df[ret1_col].rolling(window=window).corr(df[ret2_col])
        
        self.returns_data = df
        
        # Summary statistics by regime
        corr_summary = df.groupby('REGIME')[corr_col].agg([
            'mean', 'std', 'min', 'max'
        ]).round(3)
        
        print(f"✓ Rolling correlation calculated")
        print("\nCorrelation by Regime:")
        print(corr_summary)
        
        return df
    
    def calculate_portfolio_returns(self, weights=None):
        """Calculate returns for a weighted portfolio"""
        if self.returns_data is None:
            raise ValueError("Must run calculate_returns() first")
        
        if weights is None:
            weights = self.config.PORTFOLIO_WEIGHTS
        
        print(f"Calculating portfolio returns with weights: {weights}")
        
        df = self.returns_data.copy()
        
        # Calculate portfolio return
        df['PORTFOLIO_RET'] = 0
        
        for ticker, weight in weights.items():
            ret_col = f'{ticker}_RET'
            if ret_col in df.columns:
                df['PORTFOLIO_RET'] += weight * df[ret_col]
        
        self.returns_data = df
        print("✓ Portfolio returns calculated")
        
        return df
    
    def get_data(self):
        """Return data with calculated returns"""
        if self.returns_data is None:
            raise ValueError("Must run calculate_returns() first")
        return self.returns_data