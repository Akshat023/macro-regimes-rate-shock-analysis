"""
Visualization Module
Generate publication-quality charts for interview presentation
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set professional style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

class Visualizer:
    """Generate all visualizations for the analysis"""
    
    # Regime color scheme
    REGIME_COLORS = {
        'TIGHTENING': '#e74c3c',  # Red
        'EASING': '#2ecc71',       # Green
        'STRESS': '#9b59b6',       # Purple
        'NORMAL': '#3498db'        # Blue
    }
    
    def __init__(self, data, performance_df, shock_table, config):
        self.data = data
        self.performance_df = performance_df
        self.shock_table = shock_table
        self.config = config
        
    def plot_regime_timeline(self):
        """Chart 1: Regime timeline with SPY and VIX"""
        print("  Creating regime timeline...")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
        
        # Top panel: SPY with regime background
        ax1.plot(self.data.index, self.data['SPY'], 
                color='black', linewidth=1.5, label='SPY', alpha=0.8)
        
        # Add regime shading
        for regime, color in self.REGIME_COLORS.items():
            mask = self.data['REGIME'] == regime
            if mask.any():
                ax1.fill_between(self.data.index, 
                                ax1.get_ylim()[0], ax1.get_ylim()[1],
                                where=mask, alpha=0.15, color=color, label=regime)
        
        ax1.set_ylabel('SPY Price ($)', fontweight='bold')
        ax1.set_title('Macro Regime Timeline: SPY Performance Across Market Regimes',
                     fontsize=14, fontweight='bold', pad=15)
        ax1.legend(loc='upper left', frameon=True, shadow=True, ncol=5)
        ax1.grid(True, alpha=0.3)
        
        # Bottom panel: VIX
        ax2.plot(self.data.index, self.data['VIX'], 
                color='#ff6b35', linewidth=1.5, label='VIX', alpha=0.8)
        ax2.axhline(y=self.config.VIX_STRESS_THRESHOLD, 
                   color='red', linestyle='--', linewidth=2,
                   label=f'Stress Threshold ({self.config.VIX_STRESS_THRESHOLD})')
        ax2.fill_between(self.data.index, 0, self.config.VIX_STRESS_THRESHOLD,
                        alpha=0.1, color='green', label='Normal Volatility')
        ax2.fill_between(self.data.index, self.config.VIX_STRESS_THRESHOLD, 
                        self.data['VIX'].max(),
                        alpha=0.1, color='red', label='Stress Zone')
        
        ax2.set_ylabel('VIX Level', fontweight='bold')
        ax2.set_xlabel('Date', fontweight='bold')
        ax2.legend(loc='upper left', frameon=True, shadow=True)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_returns_distribution(self):
        """Chart 2: Box plots of returns by regime"""
        print("  Creating returns distribution...")
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        regimes = ['TIGHTENING', 'EASING', 'STRESS', 'NORMAL']
        colors = [self.REGIME_COLORS[r] for r in regimes]
        
        for idx, ticker in enumerate(self.config.TICKERS.keys()):
            ax = axes[idx]
            ret_col = f'{ticker}_RET'
            
            if ret_col not in self.data.columns:
                continue
            
            # Prepare box plot data
            data_to_plot = [
                self.data[self.data['REGIME'] == regime][ret_col].dropna() * 100
                for regime in regimes
            ]
            
            bp = ax.boxplot(data_to_plot, labels=regimes, patch_artist=True,
                           showfliers=False, widths=0.6,
                           boxprops=dict(linewidth=1.5),
                           medianprops=dict(linewidth=2, color='darkred'),
                           whiskerprops=dict(linewidth=1.5),
                           capprops=dict(linewidth=1.5))
            
            # Color boxes
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
            ax.set_title(f'{ticker} Daily Returns by Regime', 
                        fontsize=12, fontweight='bold')
            ax.set_ylabel('Daily Return (%)', fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='x', rotation=45)
        
        plt.suptitle('Asset Return Distributions Across Macro Regimes',
                    fontsize=15, fontweight='bold', y=1.02)
        plt.tight_layout()
        return fig
    
    def plot_rolling_correlation(self):
        """Chart 3: Rolling SPY-TLT correlation"""
        print("  Creating rolling correlation...")
        
        fig, ax = plt.subplots(figsize=(16, 8))
        
        corr_col = 'SPY_TLT_CORR'
        if corr_col not in self.data.columns:
            print("    ⚠ Correlation data not found")
            return None
        
        # Plot correlation line
        ax.plot(self.data.index, self.data[corr_col], 
               color='navy', linewidth=2.5, label='60-Day Rolling Correlation', alpha=0.8)
        
        # Add regime shading
        for regime, color in self.REGIME_COLORS.items():
            mask = self.data['REGIME'] == regime
            if mask.any():
                ax.fill_between(self.data.index, -1, 1, where=mask,
                               alpha=0.12, color=color)
        
        # Reference lines
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)
        ax.axhline(y=-0.5, color='green', linestyle='--', linewidth=1.5,
                  alpha=0.7, label='Strong Negative (Diversification Works)')
        ax.axhline(y=0.5, color='red', linestyle='--', linewidth=1.5,
                  alpha=0.7, label='Strong Positive (Diversification Fails)')
        
        ax.set_ylabel('Correlation Coefficient', fontweight='bold')
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_title('SPY-TLT Rolling Correlation: When Does 60/40 Fail?',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_ylim(-1, 1)
        ax.legend(loc='lower left', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_performance_heatmaps(self):
        """Chart 4: Performance metrics heatmaps"""
        print("  Creating performance heatmaps...")
        
        metrics = ['Ann_Return_pct', 'Ann_Vol_pct', 'Sharpe', 'Max_DD_pct']
        metric_titles = ['Annualized Return (%)', 'Annualized Volatility (%)',
                        'Sharpe Ratio', 'Maximum Drawdown (%)']
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        
        for idx, (metric, title) in enumerate(zip(metrics, metric_titles)):
            ax = axes[idx]
            
            # Pivot data
            pivot = self.performance_df.pivot(
                index='Asset', 
                columns='Regime', 
                values=metric
            )
            pivot = pivot[['TIGHTENING', 'EASING', 'STRESS', 'NORMAL']]
            
            # Choose colormap
            if metric in ['Ann_Return_pct', 'Sharpe']:
                cmap = 'RdYlGn'
                center = 0
            else:
                cmap = 'RdYlGn_r'
                center = None
            
            # Create heatmap
            sns.heatmap(pivot, annot=True, fmt='.1f', cmap=cmap, center=center,
                       ax=ax, cbar_kws={'label': title},
                       linewidths=2, linecolor='white',
                       annot_kws={'fontsize': 11, 'fontweight': 'bold'})
            
            ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.tick_params(axis='x', rotation=45)
        
        plt.suptitle('Performance Metrics Across Regimes (2000-2024)',
                    fontsize=15, fontweight='bold', y=0.995)
        plt.tight_layout()
        return fig
    
    def plot_rate_shock_heatmap(self):
        """Chart 5: Rate shock scenario analysis"""
        if self.shock_table is None or len(self.shock_table) == 0:
            print("    ⚠ No shock data available")
            return None
        
        print("  Creating rate shock heatmap...")
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Prepare data
        heatmap_data = self.shock_table.set_index('Scenario')
        
        # Create heatmap
        sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn',
                   center=0, ax=ax, cbar_kws={'label': '3-Month Return (%)'},
                   linewidths=3, linecolor='white', vmin=-20, vmax=10,
                   annot_kws={'fontsize': 12, 'fontweight': 'bold'})
        
        ax.set_title('+100bps Rate Shock: Historical Analog Analysis\n' +
                    'Portfolio Impact Over 3-Month Horizon',
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('')
        ax.set_ylabel('', fontweight='bold')
        ax.tick_params(axis='x', rotation=0)
        
        # Add annotation
        fig.text(0.5, 0.02, 
                'Based on historical events where 10Y Treasury yield rose >70bps in one month',
                ha='center', fontsize=10, style='italic', color='gray')
        
        plt.tight_layout()
        return fig
    
    def plot_regime_transitions(self):
        """Chart 6: Regime transition matrix (bonus chart)"""
        print("  Creating regime transition matrix...")
        
        # Calculate transition matrix
        regimes = ['TIGHTENING', 'EASING', 'STRESS', 'NORMAL']
        transition_matrix = pd.DataFrame(0, index=regimes, columns=regimes)
        
        prev_regime = None
        for regime in self.data['REGIME']:
            if prev_regime is not None and prev_regime != regime:
                transition_matrix.loc[prev_regime, regime] += 1
            prev_regime = regime
        
        # Convert to percentages
        transition_pct = transition_matrix.div(transition_matrix.sum(axis=1), axis=0) * 100
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(transition_pct, annot=True, fmt='.1f', cmap='Blues',
                   ax=ax, cbar_kws={'label': 'Transition Probability (%)'},
                   linewidths=2, linecolor='white',
                   annot_kws={'fontsize': 11})
        
        ax.set_title('Regime Transition Matrix: Where Do We Go Next?',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('To Regime', fontweight='bold')
        ax.set_ylabel('From Regime', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def generate_all_charts(self):
        """Generate all charts and return dictionary"""
        print("\nGenerating all charts:")
        
        charts = {
            '01_regime_timeline': self.plot_regime_timeline(),
            '02_returns_distribution': self.plot_returns_distribution(),
            '03_rolling_correlation': self.plot_rolling_correlation(),
            '04_performance_heatmaps': self.plot_performance_heatmaps(),
            '05_rate_shock_heatmap': self.plot_rate_shock_heatmap(),
            '06_regime_transitions': self.plot_regime_transitions()
        }
        
        # Filter out None values
        charts = {k: v for k, v in charts.items() if v is not None}
        
        print(f"\n✓ Generated {len(charts)} charts successfully")
        return charts
    
    def save_all_charts(self, charts):
        """Save all charts to disk"""
        print("\nSaving charts to outputs/charts/:")
        
        for name, fig in charts.items():
            if fig is None:
                continue
            
            filepath = f"outputs/charts/{name}.{self.config.CHART_FORMAT}"
            fig.savefig(filepath, dpi=self.config.CHART_DPI, 
                       bbox_inches='tight', facecolor='white')
            print(f"  ✓ {name}.{self.config.CHART_FORMAT}")
            plt.close(fig)  # Free memory
        
        print(f"\n✓ All charts saved to outputs/charts/")