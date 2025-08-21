from datetime import datetime, time
from typing import List, Dict
import pandas as pd

class MarketUtils:
    """Market utility functions"""
    
    @staticmethod
    def is_market_open(check_time: datetime = None) -> bool:
        """Check if Indian stock market is open"""
        if check_time is None:
            check_time = datetime.now()
        
        # Check if it's a weekend
        if check_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Simple holiday check - you can expand this list as needed
        # Major Indian market holidays (approximate - you can add more)
        current_date = check_time.date()
        year = current_date.year
        
        # Basic holidays (this is a simplified list)
        # In production, you'd want a more comprehensive holiday calendar
        basic_holidays = [
            # You can add specific dates here if needed
            # datetime(year, 1, 26).date(),  # Republic Day
            # datetime(year, 8, 15).date(),  # Independence Day
            # datetime(year, 10, 2).date(),  # Gandhi Jayanti
        ]
        
        if current_date in basic_holidays:
            return False
        
        # Market hours: 9:15 AM to 3:30 PM
        market_open = time(9, 15)
        market_close = time(15, 30)
        current_time = check_time.time()
        
        return market_open <= current_time <= market_close
    
    @staticmethod
    def get_expiry_dates(symbol: str, year: int) -> List[datetime]:
        """Get option expiry dates for a symbol"""
        # This is a simplified version - you'd need actual expiry calendar
        expiry_dates = []
        
        # Monthly expiries (last Thursday of each month)
        for month in range(1, 13):
            # Find last Thursday of the month
            last_day = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
            while last_day.weekday() != 3:  # Thursday = 3
                last_day -= pd.Timedelta(days=1)
            expiry_dates.append(last_day.to_pydatetime())
        
        return expiry_dates
    
    @staticmethod
    def calculate_lot_size(symbol: str) -> int:
        """Get lot size for options"""
        lot_sizes = {
            'NIFTY': 25,
            'BANKNIFTY': 15,
            'FINNIFTY': 25,
            'MIDCPNIFTY': 50,
            'SENSEX': 10
        }
        
        return lot_sizes.get(symbol, 1)
    
    @staticmethod
    def generate_option_symbol(base_symbol: str, expiry_date: datetime, 
                             strike_price: int, option_type: str) -> str:
        """Generate option symbol"""
        # Format: NIFTY24JAN11000CE
        expiry_str = expiry_date.strftime('%y%b').upper()
        day = expiry_date.strftime('%d').lstrip('0')
        
        return f"{base_symbol}{expiry_str}{day}{strike_price}{option_type}"
    
    @staticmethod
    def get_instrument_keys() -> Dict[str, List[str]]:
        """Get common instrument keys for major indices"""
        return {
            'NIFTY': [
                'NSE_INDEX|Nifty 50',
                'NSE_FO|50201',  # NIFTY futures
            ],
            'BANKNIFTY': [
                'NSE_INDEX|Nifty Bank',
                'NSE_FO|26009',  # BANKNIFTY futures
            ],
            'SENSEX': [
                'BSE_INDEX|SENSEX',
            ],
            'FINNIFTY': [
                'NSE_INDEX|Nifty Fin Service',
                'NSE_FO|26037',  # FINNIFTY futures
            ]
        }