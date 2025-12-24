"""
Configuration Parameters for Macro Regimes Analysis
Modify thresholds here for sensitivity analysis
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Project-wide configuration"""
    
    # ========== DATA PARAMETERS ==========
    START_DATE = "2000-01-01"
    END_DATE = "2024-12-31"
    
    # ========== FRED API KEY (from environment) ==========
    FRED_API_KEY = os.getenv('FRED_API_KEY')  # ✅ Secure - reads from .env
    
    # ========== REGIME THRESHOLDS ==========
    # Rate change threshold (percentage points)
    RATE_CHANGE_THRESHOLD = 0.20  # 20bps quarterly change
    
    # VIX stress threshold
    VIX_STRESS_THRESHOLD = 25.0   # Level indicating market stress
    VIX_LOOKBACK = 5              # Days for VIX moving average
    
    # ... rest of your config stays the same
    
    # ========== RATE SHOCK SCENARIO ==========
    SHOCK_YIELD_THRESHOLD = 0.70  # 70bps yield increase for shock identification
    SHOCK_HORIZON = 63            # Trading days (~3 months forward)
    SHOCK_LOOKBACK = 21           # Days to measure yield change (1 month)
    
    # ========== PORTFOLIO PARAMETERS ==========
    PORTFOLIO_WEIGHTS = {
        'SPY': 0.60,  # S&P 500 exposure
        'TLT': 0.30,  # Long-term Treasury exposure
        'GLD': 0.10   # Gold hedge
    }
    
    # ========== ASSET TICKERS ==========
    TICKERS = {
        'SPY': 'S&P 500 ETF',
        'TLT': '20Y+ Treasury ETF',
        'GLD': 'Gold ETF'
    }
    
    # ========== ANALYSIS PARAMETERS ==========
    ROLLING_CORR_WINDOW = 60      # Days for rolling correlation
    QUARTERLY_LOOKBACK = 63       # Trading days (~3 months)
    ANNUALIZATION_FACTOR = 252    # Trading days per year
    
    # ========== OUTPUT SETTINGS ==========
    SAVE_CHARTS = True            # Save charts to disk
    CHART_FORMAT = 'png'          # png, pdf, or svg
    CHART_DPI = 300               # Resolution for saved charts
    
    # ========== SENSITIVITY ANALYSIS ==========
    # Alternative thresholds to test
    SENSITIVITY_THRESHOLDS = {
        'rate_change': [0.10, 0.20, 0.30],  # 10bp, 20bp, 30bp
        'vix_stress': [20.0, 25.0, 30.0]     # Different VIX levels
    }
    
    # ========== DATA SOURCES ==========
    # Note: For production, use FRED API key
    # Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
    
    # FRED series codes
    FRED_SERIES = {
        'fed_funds': 'DFF',           # Federal Funds Effective Rate
        'treasury_10y': 'DGS10',      # 10-Year Treasury Constant Maturity
        'treasury_2y': 'DGS2',        # 2-Year Treasury (optional)
    }
    
    @classmethod
    def validate(cls):
        """Validate configuration parameters"""
        assert cls.RATE_CHANGE_THRESHOLD > 0, "Rate threshold must be positive"
        assert cls.VIX_STRESS_THRESHOLD > 0, "VIX threshold must be positive"
        assert abs(sum(cls.PORTFOLIO_WEIGHTS.values()) - 1.0) < 1e-6, "Weights must sum to 1"
        assert all(w >= 0 for w in cls.PORTFOLIO_WEIGHTS.values()), "Weights must be non-negative"
        print("✓ Configuration validated successfully")