"""Test suite for analytics functionality"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.analytics_service import AnalyticsService
from app.services.data_service import DataService

class TestAnalyticsService:
    """Test cases for AnalyticsService"""
    
    @pytest.fixture
    def analytics_service(self):
        """Create an analytics service instance"""
        return AnalyticsService()
    
    @pytest.fixture
    def sample_prices(self):
        """Generate sample price data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        return pd.Series(prices, index=dates)
    
    @pytest.fixture
    def sample_pair_prices(self):
        """Generate sample pair price data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        
        # Create correlated prices
        base = np.cumsum(np.random.randn(100) * 0.5)
        price1 = 100 + base
        price2 = 50 + 0.5 * base + np.random.randn(100) * 0.3
        
        return (
            pd.Series(price1, index=dates),
            pd.Series(price2, index=dates)
        )
    
    def test_price_stats(self, analytics_service, sample_prices):
        """Test price statistics calculation"""
        stats = analytics_service.calculate_price_stats(sample_prices)
        
        assert stats is not None
        assert 'current' in stats
        assert 'high' in stats
        assert 'low' in stats
        assert 'mean' in stats
        assert 'std' in stats
        assert stats['high'] >= stats['low']
        assert stats['current'] == sample_prices.iloc[-1]
    
    def test_zscore(self, analytics_service, sample_prices):
        """Test z-score calculation"""
        zscore = analytics_service.calculate_zscore(sample_prices, window=20)
        
        assert len(zscore) > 0
        assert zscore.isna().sum() == 19  # First 19 values should be NaN
        assert abs(zscore.iloc[-1]) < 10  # Z-score should be reasonable
    
    def test_adf_test(self, analytics_service, sample_prices):
        """Test ADF stationarity test"""
        result = analytics_service.calculate_adf_test(sample_prices, max_lag=5)
        
        assert result is not None
        assert 'test_statistic' in result
        assert 'p_value' in result
        assert 'is_stationary' in result
        assert isinstance(result['is_stationary'], bool)
    
    def test_ols_regression(self, analytics_service, sample_pair_prices):
        """Test OLS regression"""
        y, x = sample_pair_prices
        result = analytics_service.calculate_ols_regression(y, x)
        
        assert result is not None
        assert 'alpha' in result
        assert 'beta' in result
        assert 'r_squared' in result
        assert 0 <= result['r_squared'] <= 1
    
    def test_robust_regression_huber(self, analytics_service, sample_pair_prices):
        """Test Huber robust regression"""
        y, x = sample_pair_prices
        result = analytics_service.calculate_robust_regression(y, x, method='huber')
        
        assert result is not None
        assert 'intercept' in result
        assert 'coefficient' in result
        assert 'r_squared' in result
        assert result['method'] == 'huber'
    
    def test_robust_regression_theil_sen(self, analytics_service, sample_pair_prices):
        """Test Theil-Sen robust regression"""
        y, x = sample_pair_prices
        result = analytics_service.calculate_robust_regression(y, x, method='theil-sen')
        
        assert result is not None
        assert 'intercept' in result
        assert 'coefficient' in result
        assert result['method'] == 'theil-sen'
    
    def test_spread_calculation(self, analytics_service, sample_pair_prices):
        """Test spread calculation"""
        y, x = sample_pair_prices
        
        # Test ratio spread
        spread_ratio = analytics_service.calculate_spread(y, x, method='ratio')
        assert len(spread_ratio) > 0
        assert spread_ratio.isna().sum() == 0
        
        # Test OLS spread
        spread_ols = analytics_service.calculate_spread(y, x, method='ols')
        assert len(spread_ols) > 0
    
    def test_rolling_correlation(self, analytics_service, sample_pair_prices):
        """Test rolling correlation calculation"""
        x, y = sample_pair_prices
        corr = analytics_service.calculate_rolling_correlation(x, y, window=20)
        
        assert len(corr) > 0
        assert corr.isna().sum() == 19  # First 19 values should be NaN
        assert all(corr.dropna() >= -1) and all(corr.dropna() <= 1)
    
    def test_cointegration(self, analytics_service, sample_pair_prices):
        """Test cointegration test"""
        y, x = sample_pair_prices
        result = analytics_service.calculate_cointegration(y, x)
        
        assert result is not None
        assert 'test_statistic' in result
        assert 'p_value' in result
        assert 'is_cointegrated' in result
        assert isinstance(result['is_cointegrated'], bool)
    
    def test_technical_indicators(self, analytics_service):
        """Test technical indicators calculation"""
        dates = pd.date_range(start='2023-01-01', periods=200, freq='1H')
        df = pd.DataFrame({
            'open': 100 + np.random.randn(200).cumsum(),
            'high': 102 + np.random.randn(200).cumsum(),
            'low': 98 + np.random.randn(200).cumsum(),
            'close': 100 + np.random.randn(200).cumsum(),
            'volume': np.random.rand(200) * 1000
        }, index=dates)
        
        result = analytics_service.calculate_technical_indicators(df)
        
        assert len(result) == len(df)
        assert 'sma_5' in result.columns
        assert 'ema_9' in result.columns
        assert 'rsi' in result.columns
        assert 'macd' in result.columns
        assert 'bb_upper' in result.columns
        assert 'bb_lower' in result.columns
    
    def test_empty_series(self, analytics_service):
        """Test handling of empty series"""
        empty_series = pd.Series(dtype=float)
        
        stats = analytics_service.calculate_price_stats(empty_series)
        assert stats == {}
        
        zscore = analytics_service.calculate_zscore(empty_series)
        assert len(zscore) == 0
    
    def test_short_series(self, analytics_service):
        """Test handling of series shorter than window"""
        short_series = pd.Series([1, 2, 3])
        
        zscore = analytics_service.calculate_zscore(short_series, window=20)
        assert len(zscore) == 0

class TestDataService:
    """Test cases for DataService"""
    
    @pytest.fixture
    def data_service(self):
        """Create a data service instance"""
        # Note: This would require a test database setup
        # For now, we'll skip these tests
        pass
    
    def test_placeholder(self):
        """Placeholder test"""
        assert True

class TestAlertService:
    """Test cases for AlertService"""
    
    def test_placeholder(self):
        """Placeholder test"""
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
