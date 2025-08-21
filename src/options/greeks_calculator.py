# ==================== src/options/greeks_calculator.py ====================
import math
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from scipy.stats import norm

class GreeksCalculator:
    """Calculate option Greeks using Black-Scholes model"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_greeks(self, option_data: Dict) -> Dict:
        """Calculate option Greeks for risk assessment"""
        try:
            # Extract required parameters
            spot_price = option_data.get('spot_price', 0)
            strike_price = option_data.get('strike_price', 0)
            time_to_expiry = option_data.get('time_to_expiry', 0)  # in years
            risk_free_rate = option_data.get('risk_free_rate', 0.06)  # 6% default
            volatility = option_data.get('implied_volatility', 0.20)  # 20% default
            option_type = option_data.get('option_type', 'CE').upper()
            current_premium = option_data.get('current_premium', 0)
            
            if not all([spot_price, strike_price, time_to_expiry]):
                self.logger.warning("Insufficient data for Greeks calculation")
                return self._get_default_greeks()
            
            # Calculate Greeks using Black-Scholes
            greeks = self._black_scholes_greeks(
                spot_price, strike_price, time_to_expiry, 
                risk_free_rate, volatility, option_type
            )
            
            # Add additional risk metrics
            greeks.update({
                'theoretical_price': greeks.get('option_price', 0),
                'current_premium': current_premium,
                'intrinsic_value': self._calculate_intrinsic_value(spot_price, strike_price, option_type),
                'time_value': current_premium - self._calculate_intrinsic_value(spot_price, strike_price, option_type),
                'moneyness': self._calculate_moneyness(spot_price, strike_price, option_type),
                'risk_score': self._calculate_risk_score(greeks, time_to_expiry)
            })
            
            return greeks
            
        except Exception as e:
            self.logger.error(f"Error calculating Greeks: {e}")
            return self._get_default_greeks()
    
    def _black_scholes_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict:
        """Calculate Greeks using Black-Scholes model"""
        try:
            # Avoid division by zero
            if T <= 0 or sigma <= 0:
                return self._get_default_greeks()
            
            # Calculate d1 and d2
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            # Standard normal CDF and PDF
            N_d1 = norm.cdf(d1)
            N_d2 = norm.cdf(d2)
            n_d1 = norm.pdf(d1)  # PDF for Greeks calculation
            
            if option_type == 'CE':
                # Call option
                option_price = S * N_d1 - K * math.exp(-r * T) * N_d2
                delta = N_d1
                theta = (-S * n_d1 * sigma / (2 * math.sqrt(T)) 
                        - r * K * math.exp(-r * T) * N_d2) / 365  # Per day
            else:
                # Put option  
                option_price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                delta = N_d1 - 1
                theta = (-S * n_d1 * sigma / (2 * math.sqrt(T)) 
                        + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365  # Per day
            
            # Common Greeks (same for both CE and PE)
            gamma = n_d1 / (S * sigma * math.sqrt(T))
            vega = S * n_d1 * math.sqrt(T) / 100  # Per 1% change in volatility
            rho = K * T * math.exp(-r * T) * (N_d2 if option_type == 'CE' else norm.cdf(-d2)) / 100
            
            return {
                'option_price': round(option_price, 2),
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),
                'theta': round(theta, 2),
                'vega': round(vega, 2),
                'rho': round(rho, 4)
            }
            
        except Exception as e:
            self.logger.error(f"Error in Black-Scholes calculation: {e}")
            return self._get_default_greeks()
    
    def _calculate_intrinsic_value(self, spot_price: float, strike_price: float, option_type: str) -> float:
        """Calculate intrinsic value of option"""
        if option_type == 'CE':
            return max(0, spot_price - strike_price)
        else:  # PE
            return max(0, strike_price - spot_price)
    
    def _calculate_moneyness(self, spot_price: float, strike_price: float, option_type: str) -> str:
        """Determine if option is ITM, ATM, or OTM"""
        if option_type == 'CE':
            if spot_price > strike_price:
                return "ITM"
            elif abs(spot_price - strike_price) <= 50:  # Within 50 points
                return "ATM"
            else:
                return "OTM"
        else:  # PE
            if spot_price < strike_price:
                return "ITM"
            elif abs(spot_price - strike_price) <= 50:
                return "ATM"
            else:
                return "OTM"
    
    def _calculate_risk_score(self, greeks: Dict, time_to_expiry: float) -> str:
        """Calculate overall risk score based on Greeks"""
        try:
            delta = abs(greeks.get('delta', 0))
            theta = abs(greeks.get('theta', 0))
            gamma = greeks.get('gamma', 0)
            
            risk_score = 0
            
            # Delta risk (higher delta = higher directional risk)
            if delta > 0.7:
                risk_score += 3
            elif delta > 0.4:
                risk_score += 2
            else:
                risk_score += 1
            
            # Theta risk (time decay)
            if theta > 20:
                risk_score += 3
            elif theta > 10:
                risk_score += 2
            else:
                risk_score += 1
            
            # Time to expiry risk
            if time_to_expiry < 0.02:  # Less than 1 week
                risk_score += 3
            elif time_to_expiry < 0.08:  # Less than 1 month
                risk_score += 2
            else:
                risk_score += 1
            
            # Return risk category
            if risk_score >= 7:
                return "HIGH"
            elif risk_score >= 5:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            return "UNKNOWN"
    
    def _get_default_greeks(self) -> Dict:
        """Return default Greeks when calculation fails"""
        return {
            'option_price': 0,
            'delta': 0,
            'gamma': 0,
            'theta': 0,
            'vega': 0,
            'rho': 0,
            'intrinsic_value': 0,
            'time_value': 0,
            'moneyness': 'UNKNOWN',
            'risk_score': 'UNKNOWN'
        }
    
    def calculate_time_to_expiry(self, expiry_date: str) -> float:
        """Calculate time to expiry in years"""
        try:
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            now = datetime.now()
            
            # Market closes at 3:30 PM
            market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            if now.time() > market_close.time():
                now = market_close
            
            time_diff = expiry - now
            return max(0, time_diff.total_seconds() / (365.25 * 24 * 3600))
            
        except Exception as e:
            self.logger.error(f"Error calculating time to expiry: {e}")
            return 0.02  # Default to 1 week

    def get_estimated_volatility(self, symbol: str) -> float:
        """Get estimated implied volatility for the symbol"""
        # Default volatilities based on historical data
        volatility_map = {
            'NIFTY': 0.18,      # 18%
            'BANKNIFTY': 0.22,  # 22%
            'SENSEX': 0.16      # 16%
        }
        
        return volatility_map.get(symbol, 0.20)  # Default 20%