"""
Regime Classification Module
Rule-based identification of macro regimes
"""

import pandas as pd
import numpy as np

class RegimeClassifier:
    """Classify market regimes using transparent rules"""
    
    def __init__(self, data, config):
        self.data = data.copy()
        self.config = config
        self.regime_data = None
        
    def classify_regimes(self):
        """
        Assign regime labels based on transparent rules
        Hierarchy: STRESS > TIGHTENING > EASING > NORMAL
        
        No lookahead bias: uses only data available at time t
        """
        print("Classifying macro regimes...")
        
        df = self.data.copy()
        
        # Calculate quarterly rate changes (no lookahead)
        lookback = self.config.QUARTERLY_LOOKBACK
        df['RATE_CHANGE_QTR'] = df['FED_FUNDS'].diff(lookback)
        df['YIELD_CHANGE_QTR'] = df['TREASURY_10Y'].diff(lookback)
        
        # VIX moving average (trailing only)
        df['VIX_MA'] = df['VIX'].rolling(
            window=self.config.VIX_LOOKBACK, 
            min_periods=1
        ).mean()
        
        # Initialize regime column
        df['REGIME'] = 'NORMAL'
        
        # Apply classification rules
        threshold = self.config.RATE_CHANGE_THRESHOLD
        vix_threshold = self.config.VIX_STRESS_THRESHOLD
        
        for i in range(lookback, len(df)):
            vix_level = df['VIX_MA'].iloc[i]
            rate_chg = df['RATE_CHANGE_QTR'].iloc[i]
            yield_chg = df['YIELD_CHANGE_QTR'].iloc[i]
            
            # Priority 1: Stress (overrides everything)
            if pd.notna(vix_level) and vix_level > vix_threshold:
                regime = 'STRESS'
            
            # Priority 2: Tightening
            elif (pd.notna(rate_chg) and rate_chg > threshold) or \
                 (pd.notna(yield_chg) and yield_chg > threshold):
                regime = 'TIGHTENING'
            
            # Priority 3: Easing
            elif (pd.notna(rate_chg) and rate_chg < -threshold) or \
                 (pd.notna(yield_chg) and yield_chg < -threshold):
                regime = 'EASING'
            
            # Default: Normal
            else:
                regime = 'NORMAL'
            
            df.loc[df.index[i], 'REGIME'] = regime
        
        self.regime_data = df
        
        # Print classification summary
        regime_counts = df['REGIME'].value_counts()
        print(f"✓ Regimes classified: {len(df)} days")
        for regime, count in regime_counts.items():
            pct = count / len(df) * 100
            print(f"  {regime:12s}: {count:5d} days ({pct:5.1f}%)")
        
        return df
    
    def get_regime_summary(self):
        """Calculate detailed regime statistics"""
        if self.regime_data is None:
            raise ValueError("Must run classify_regimes() first")
        
        df = self.regime_data
        
        # Count and percentage
        regime_counts = df['REGIME'].value_counts()
        regime_pcts = (regime_counts / len(df) * 100).round(2)
        
        # Average duration (consecutive days in same regime)
        durations = []
        current_regime = None
        current_duration = 0
        
        for regime in df['REGIME']:
            if regime == current_regime:
                current_duration += 1
            else:
                if current_regime is not None:
                    durations.append({
                        'regime': current_regime,
                        'duration': current_duration
                    })
                current_regime = regime
                current_duration = 1
        
        # Add last regime
        if current_regime is not None:
            durations.append({
                'regime': current_regime,
                'duration': current_duration
            })
        
        duration_df = pd.DataFrame(durations)
        avg_duration = duration_df.groupby('regime')['duration'].mean()
        
        # Combine statistics
        summary = pd.DataFrame({
            'Days': regime_counts,
            'Percentage': regime_pcts,
            'Avg_Duration_Days': avg_duration
        }).round(1)
        
        return summary.sort_values('Days', ascending=False)
    
    def identify_regime_transitions(self):
        """Identify when regimes change"""
        if self.regime_data is None:
            raise ValueError("Must run classify_regimes() first")
        
        df = self.regime_data
        
        # Find transition points
        df['REGIME_SHIFT'] = (df['REGIME'] != df['REGIME'].shift(1))
        transitions = df[df['REGIME_SHIFT']].copy()
        
        # Add previous regime
        transitions['PREV_REGIME'] = df['REGIME'].shift(1)[df['REGIME_SHIFT']]
        
        # Select relevant columns
        transition_summary = transitions[[
            'REGIME', 'PREV_REGIME', 'VIX', 'FED_FUNDS', 'TREASURY_10Y'
        ]].copy()
        
        return transition_summary
    
    def get_data(self):
        """Return regime-classified data"""
        if self.regime_data is None:
            raise ValueError("Must run classify_regimes() first")
        return self.regime_data