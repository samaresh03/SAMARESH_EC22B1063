import logging
import json
from typing import List, Dict, Tuple, Optional, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from sklearn.linear_model import HuberRegressor, TheilSenRegressor

from .data_service import DataService
from ..config import ANALYTICS_CONFIG

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for performing quantitative analytics on market data"""
    
    def __init__(self, data_service: DataService = None):
        self.data_service = data_service or DataService()
    
    def calculate_price_stats(self, prices: pd.Series) -> Dict:
        """Calculate basic price statistics"""
        if prices.empty:
            return {}
            
        returns = prices.pct_change().dropna()
        
        return {
            'current': float(prices.iloc[-1]) if len(prices) > 0 else None,
            'open': float(prices.iloc[0]) if len(prices) > 0 else None,
            'high': float(prices.max()) if len(prices) > 0 else None,
            'low': float(prices.min()) if len(prices) > 0 else None,
            'mean': float(prices.mean()) if len(prices) > 0 else None,
            'std': float(prices.std()) if len(prices) > 0 else None,
            'returns_mean': float(returns.mean()) if len(returns) > 0 else None,
            'returns_std': float(returns.std()) if len(returns) > 0 else None,
            'sharpe_ratio': float(returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 1 else None,
            'count': len(prices)
        }
    
    def calculate_ols_regression(self, y: pd.Series, x: pd.Series) -> Dict:
        """
        Perform OLS regression y = alpha + beta * x + epsilon
        
        Args:
            y: Dependent variable
            x: Independent variable
            
        Returns:
            Dictionary with regression results
        """
        if len(x) < 2 or len(y) < 2:
            return {}
            
        # Align x and y by index
        aligned = pd.concat([y, x], axis=1).dropna()
        if len(aligned) < 2:
            return {}
            
        y_aligned = aligned.iloc[:, 0]
        x_aligned = aligned.iloc[:, 1]
        
        try:
            # Add constant for intercept
            X = sm.add_constant(x_aligned)
            model = OLS(y_aligned, X).fit()
            
            return {
                'alpha': model.params[0],
                'beta': model.params[1],
                'r_squared': model.rsquared,
                'p_value': model.f_pvalue,
                'std_err': model.bse[1],
                'residuals': model.resid.tolist()
            }
        except Exception as e:
            logger.error(f"Error in OLS regression: {e}")
            return {}
    
    def calculate_robust_regression(self, y: pd.Series, x: pd.Series, method: str = 'huber') -> Dict:
        """
        Perform robust regression (Huber or Theil-Sen)
        
        Args:
            y: Dependent variable
            x: Independent variable
            method: 'huber' or 'theil-sen'
            
        Returns:
            Dictionary with regression results
        """
        if len(x) < 2 or len(y) < 2:
            return {}
            
        # Align x and y by index
        aligned = pd.concat([y, x], axis=1).dropna()
        if len(aligned) < 2:
            return {}
            
        y_aligned = aligned.iloc[:, 0].values.reshape(-1, 1)
        x_aligned = aligned.iloc[:, 1].values.reshape(-1, 1)
        
        try:
            if method.lower() == 'huber':
                model = HuberRegressor()
            else:  # theil-sen
                model = TheilSenRegressor()
                
            model.fit(x_aligned, y_aligned)
            
            # Calculate R-squared
            y_pred = model.predict(x_aligned)
            ss_res = np.sum((y_aligned - y_pred) ** 2)
            ss_tot = np.sum((y_aligned - np.mean(y_aligned)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return {
                'intercept': float(model.intercept_[0]) if hasattr(model.intercept_, '__len__') else float(model.intercept_),
                'coefficient': float(model.coef_[0]) if hasattr(model.coef_[0], '__len__') else float(model.coef_[0]),
                'r_squared': float(r_squared),
                'method': method
            }
            
        except Exception as e:
            logger.error(f"Error in {method} regression: {e}")
            return {}
    
    def calculate_spread(self, y: pd.Series, x: pd.Series, method: str = 'ols') -> pd.Series:
        """
        Calculate spread between two price series using specified method
        
        Args:
            y: First price series
            x: Second price series
            method: 'ols' for OLS residuals, 'ratio' for price ratio
            
        Returns:
            Spread series
        """
        if method == 'ratio':
            return y / x
        else:  # OLS
            result = self.calculate_ols_regression(y, x)
            if not result:
                return pd.Series(dtype=float)
            return pd.Series(result['residuals'], index=y.index[-len(result['residuals']):])
    
    def calculate_zscore(self, series: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate z-score of a series
        
        Args:
            series: Input series
            window: Rolling window size
            
        Returns:
            Z-score series
        """
        if len(series) < window:
            return pd.Series(dtype=float)
            
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        zscore = (series - rolling_mean) / rolling_std
        return zscore
    
    def calculate_adf_test(self, series: pd.Series, max_lag: int = 5) -> Dict:
        """
        Perform Augmented Dickey-Fuller test for stationarity
        
        Args:
            series: Time series to test
            max_lag: Maximum lag to include in the test
            
        Returns:
            Dictionary with test results
        """
        if len(series) < max_lag + 2:  # Need at least max_lag + 2 observations
            return {}
            
        try:
            result = adfuller(series, maxlag=max_lag)
            
            return {
                'test_statistic': result[0],
                'p_value': result[1],
                'used_lag': result[2],
                'n_obs': result[3],
                'critical_values': result[4],
                'is_stationary': result[1] < 0.05  # 95% confidence
            }
        except Exception as e:
            logger.error(f"Error in ADF test: {e}")
            return {}
    
    def calculate_cointegration(self, y: pd.Series, x: pd.Series) -> Dict:
        """
        Test for cointegration between two price series
        
        Args:
            y: First price series
            x: Second price series
            
        Returns:
            Dictionary with cointegration test results
        """
        if len(x) < 2 or len(y) < 2:
            return {}
            
        # Align x and y by index
        aligned = pd.concat([y, x], axis=1).dropna()
        if len(aligned) < 2:
            return {}
            
        y_aligned = aligned.iloc[:, 0]
        x_aligned = aligned.iloc[:, 1]
        
        try:
            result = coint(y_aligned, x_aligned)
            
            return {
                'test_statistic': result[0],
                'p_value': result[1],
                'critical_values': result[2],
                'is_cointegrated': result[1] < 0.05  # 95% confidence
            }
        except Exception as e:
            logger.error(f"Error in cointegration test: {e}")
            return {}
    
    def calculate_rolling_correlation(
        self, 
        x: pd.Series, 
        y: pd.Series, 
        window: int = 30
    ) -> pd.Series:
        """
        Calculate rolling correlation between two series
        
        Args:
            x: First series
            y: Second series
            window: Rolling window size
            
        Returns:
            Series of rolling correlations
        """
        if len(x) < window or len(y) < window:
            return pd.Series(dtype=float)
            
        # Align x and y by index
        aligned = pd.concat([x, y], axis=1).dropna()
        if len(aligned) < window:
            return pd.Series(dtype=float)
            
        return aligned.iloc[:, 0].rolling(window=window).corr(aligned.iloc[:, 1])
    
    def calculate_rolling_beta(
        self, 
        y: pd.Series, 
        x: pd.Series, 
        window: int = 30
    ) -> pd.Series:
        """
        Calculate rolling beta (sensitivity of y to x)
        
        Args:
            y: Dependent variable (e.g., asset returns)
            x: Independent variable (e.g., market returns)
            window: Rolling window size
            
        Returns:
            Series of rolling betas
        """
        if len(x) < window or len(y) < window:
            return pd.Series(dtype=float)
            
        # Align x and y by index
        aligned = pd.concat([y, x], axis=1).dropna()
        if len(aligned) < window:
            return pd.Series(dtype=float)
            
        betas = []
        for i in range(window, len(aligned) + 1):
            window_data = aligned.iloc[i-window:i]
            x_values = window_data.iloc[:, 1].values.reshape(-1, 1)
            y_values = window_data.iloc[:, 0].values
            
            # Add intercept
            X = np.column_stack((np.ones_like(x_values), x_values))
            
            try:
                beta = np.linalg.lstsq(X, y_values, rcond=None)[0][1]
                betas.append(beta)
            except:
                betas.append(np.nan)
        
        return pd.Series(betas, index=aligned.index[window-1:])
    
    def calculate_technical_indicators(
        self, 
        df: pd.DataFrame, 
        price_col: str = 'close',
        volume_col: str = 'volume'
    ) -> pd.DataFrame:
        """
        Calculate various technical indicators
        
        Args:
            df: DataFrame with price and volume data
            price_col: Name of the price column
            volume_col: Name of the volume column
            
        Returns:
            DataFrame with added technical indicators
        """
        if df.empty:
            return df
            
        result = df.copy()
        
        # Simple Moving Averages
        for period in [5, 10, 20, 50, 200]:
            result[f'sma_{period}'] = result[price_col].rolling(window=period).mean()
        
        # Exponential Moving Averages
        for period in [9, 21, 50]:
            result[f'ema_{period}'] = result[price_col].ewm(span=period, adjust=False).mean()
        
        # Bollinger Bands
        window = 20
        result['sma_20'] = result[price_col].rolling(window=window).mean()
        result['bb_upper'] = result['sma_20'] + 2 * result[price_col].rolling(window=window).std()
        result['bb_lower'] = result['sma_20'] - 2 * result[price_col].rolling(window=window).std()
        
        # RSI
        delta = result[price_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = result[price_col].ewm(span=12, adjust=False).mean()
        exp2 = result[price_col].ewm(span=26, adjust=False).mean()
        result['macd'] = exp1 - exp2
        result['macd_signal'] = result['macd'].ewm(span=9, adjust=False).mean()
        result['macd_hist'] = result['macd'] - result['macd_signal']
        
        # Volume Weighted Average Price (VWAP) - typically for intraday data
        if 'volume' in result.columns and 'high' in result.columns and 'low' in result.columns:
            typical_price = (result['high'] + result['low'] + result[price_col]) / 3
            result['vwap'] = (typical_price * result['volume']).cumsum() / result['volume'].cumsum()
        
        return result
    
    def calculate_metrics_for_symbols(
        self, 
        symbol1: str, 
        symbol2: str = None, 
        timeframe: str = '1m',
        window: int = 20
    ) -> Dict:
        """
        Calculate all relevant metrics for one or two symbols
        
        Args:
            symbol1: First symbol
            symbol2: Optional second symbol for pair analysis
            timeframe: Timeframe for analysis
            window: Window size for rolling calculations
            
        Returns:
            Dictionary with all calculated metrics
        """
        # Get OHLCV data
        df1 = self.data_service.get_ohlcv(symbol1, timeframe=timeframe)
        
        if df1.empty:
            return {}
        
        result = {
            'symbol1': symbol1,
            'symbol2': symbol2,
            'timeframe': timeframe,
            'window': window,
            'price_stats': {},
            'technical_indicators': {},
            'pair_metrics': {}
        }
        
        # Single symbol metrics
        result['price_stats'][symbol1] = self.calculate_price_stats(df1['close'])
        
        # Technical indicators
        result['technical_indicators'][symbol1] = self.calculate_technical_indicators(df1)
        
        if symbol2:
            df2 = self.data_service.get_ohlcv(symbol2, timeframe=timeframe)
            
            if not df2.empty:
                result['price_stats'][symbol2] = self.calculate_price_stats(df2['close'])
                result['technical_indicators'][symbol2] = self.calculate_technical_indicators(df2)
                
                # Pair metrics
                aligned = pd.concat([
                    df1['close'].rename(symbol1), 
                    df2['close'].rename(symbol2)
                ], axis=1).dropna()
                
                if not aligned.empty:
                    # OLS regression
                    ols_result = self.calculate_ols_regression(
                        y=aligned[symbol1],
                        x=aligned[symbol2]
                    )
                    
                    # Robust regression
                    huber_result = self.calculate_robust_regression(
                        y=aligned[symbol1],
                        x=aligned[symbol2],
                        method='huber'
                    )
                    
                    # Spread and z-score
                    spread = self.calculate_spread(
                        y=aligned[symbol1],
                        x=aligned[symbol2],
                        method='ratio'  # or 'ols'
                    )
                    
                    zscore = self.calculate_zscore(spread, window=window)
                    
                    # Cointegration test
                    coint_result = self.calculate_cointegration(
                        y=aligned[symbol1],
                        x=aligned[symbol2]
                    )
                    
                    # Rolling correlation
                    rolling_corr = self.calculate_rolling_correlation(
                        x=aligned[symbol1],
                        y=aligned[symbol2],
                        window=window
                    )
                    
                    result['pair_metrics'].update({
                        'ols_regression': ols_result,
                        'huber_regression': huber_result,
                        'spread': spread.dropna().tolist(),
                        'zscore': zscore.dropna().tolist(),
                        'cointegration': coint_result,
                        'rolling_correlation': rolling_corr.dropna().tolist(),
                        'timestamps': aligned.index.astype(str).tolist()
                    })
        
        return result
