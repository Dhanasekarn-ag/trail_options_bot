# ==================== scripts/backtest.py ====================
#!/usr/bin/env python3
"""
Backtesting script for strategies
"""
import sys
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config.settings import get_settings
from src.strategy.base_strategy import BaseStrategy
from src.models.order import Order, OrderType, TransactionType, OrderStatus
from src.models.position import Position

class BacktestEngine:
    """Backtesting engine"""
    
    def __init__(self, initial_capital: float, start_date: str, end_date: str):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        self.trades = []
        self.portfolio_values = []
        self.positions = {}
        self.max_drawdown = 0
        self.peak_value = initial_capital
        
    def load_historical_data(self, symbol: str) -> pd.DataFrame:
        """Load historical data for backtesting"""
        # This is a placeholder - you'll need to implement actual data loading
        # You can use yfinance, Alpha Vantage, or other data sources
        
        # Generate sample data for demonstration
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='1min')
        np.random.seed(42)
        
        # Generate realistic option price data
        base_price = 100
        price_changes = np.random.normal(0, 2, len(dates))
        prices = base_price + np.cumsum(price_changes)
        prices = np.maximum(prices, 1)  # Ensure positive prices
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * (1 + np.random.uniform(0, 0.02, len(prices))),
            'low': prices * (1 - np.random.uniform(0, 0.02, len(prices))),
            'close': prices,
            'volume': np.random.randint(100, 10000, len(prices))
        })
        
        return data
    
    async def run_backtest(self, strategy: BaseStrategy, symbol: str):
        """Run backtest for a strategy"""
        print(f"Running backtest for {strategy.name} on {symbol}")
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Initial Capital: ₹{self.initial_capital:,.2f}")
        
        # Load historical data
        data = self.load_historical_data(symbol)
        
        for index, row in data.iterrows():
            current_time = row['timestamp']
            market_data = {
                'symbol': symbol,
                'price': row['close'],
                'high': row['high'],
                'low': row['low'],
                'volume': row['volume'],
                'timestamp': current_time
            }
            
            # Check for entry signals
            entry_order = await strategy.should_enter(market_data)
            if entry_order:
                await self.execute_order(entry_order, market_data)
            
            # Check for exit signals
            for position_key, position in list(self.positions.items()):
                exit_order = await strategy.should_exit(position, market_data)
                if exit_order:
                    await self.execute_order(exit_order, market_data)
            
            # Update portfolio value
            portfolio_value = self.calculate_portfolio_value(market_data)
            self.portfolio_values.append({
                'timestamp': current_time,
                'value': portfolio_value
            })
            
            # Update drawdown
            if portfolio_value > self.peak_value:
                self.peak_value = portfolio_value
            else:
                drawdown = (self.peak_value - portfolio_value) / self.peak_value
                if drawdown > self.max_drawdown:
                    self.max_drawdown = drawdown
        
        # Generate results
        self.generate_results()
    
    async def execute_order(self, order: Order, market_data: dict):
        """Execute order in backtest"""
        try:
            # Simulate order execution
            execution_price = market_data['price']
            
            if order.transaction_type == TransactionType.BUY:
                cost = order.quantity * execution_price
                if cost <= self.current_capital:
                    # Create position
                    position = Position(
                        symbol=order.symbol,
                        quantity=order.quantity,
                        average_price=execution_price,
                        current_price=execution_price,
                        pnl=0,
                        unrealized_pnl=0,
                        instrument_key=order.instrument_key or order.symbol,
                        entry_time=market_data['timestamp']
                    )
                    
                    self.positions[order.symbol] = position
                    self.current_capital -= cost
                    
                    self.trades.append({
                        'timestamp': market_data['timestamp'],
                        'symbol': order.symbol,
                        'action': 'BUY',
                        'quantity': order.quantity,
                        'price': execution_price,
                        'value': cost
                    })
                    
            elif order.transaction_type == TransactionType.SELL:
                if order.symbol in self.positions:
                    position = self.positions[order.symbol]
                    sell_value = order.quantity * execution_price
                    
                    # Calculate P&L
                    cost_basis = position.quantity * position.average_price
                    pnl = sell_value - cost_basis
                    
                    # Close position
                    del self.positions[order.symbol]
                    self.current_capital += sell_value
                    
                    self.trades.append({
                        'timestamp': market_data['timestamp'],
                        'symbol': order.symbol,
                        'action': 'SELL',
                        'quantity': order.quantity,
                        'price': execution_price,
                        'value': sell_value,
                        'pnl': pnl
                    })
                    
        except Exception as e:
            print(f"Error executing order: {e}")
    
    def calculate_portfolio_value(self, market_data: dict):
        """Calculate current portfolio value"""
        portfolio_value = self.current_capital
        
        for position in self.positions.values():
            if position.symbol == market_data['symbol']:
                portfolio_value += position.quantity * market_data['price']
        
        return portfolio_value
    
    def generate_results(self):
        """Generate backtest results"""
        if not self.trades:
            print("No trades executed during backtest period")
            return
        
        trades_df = pd.DataFrame(self.trades)
        portfolio_df = pd.DataFrame(self.portfolio_values)
        
        # Calculate metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df.get('pnl', 0) > 0])
        losing_trades = len(trades_df[trades_df.get('pnl', 0) < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum() if 'pnl' in trades_df.columns else 0
        final_value = portfolio_df['value'].iloc[-1] if not portfolio_df.empty else self.initial_capital
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        # Print results
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"Initial Capital: ₹{self.initial_capital:,.2f}")
        print(f"Final Value: ₹{final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Total P&L: ₹{total_pnl:,.2f}")
        print(f"Max Drawdown: {self.max_drawdown:.2%}")
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        
        # Plot results
        self.plot_results(portfolio_df)
    
    def plot_results(self, portfolio_df: pd.DataFrame):
        """Plot backtest results"""
        plt.figure(figsize=(12, 8))
        
        # Portfolio value over time
        plt.subplot(2, 1, 1)
        plt.plot(portfolio_df['timestamp'], portfolio_df['value'])
        plt.title('Portfolio Value Over Time')
        plt.ylabel('Value (₹)')
        plt.grid(True)
        
        # Drawdown
        plt.subplot(2, 1, 2)
        portfolio_df['peak'] = portfolio_df['value'].expanding().max()
        portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['peak']) / portfolio_df['peak']
        plt.fill_between(portfolio_df['timestamp'], portfolio_df['drawdown'], 0, alpha=0.3, color='red')
        plt.title('Drawdown')
        plt.ylabel('Drawdown %')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

async def main():
    """Main backtesting function"""
    settings = get_settings()
    
    # Initialize backtest engine
    engine = BacktestEngine(
        initial_capital=settings.backtest_initial_capital,
        start_date=settings.backtest_start_date,
        end_date=settings.backtest_end_date
    )
    
    # You'll implement your strategy here
    # from src.strategy.options_strategy import OptionsStrategy
    # strategy = OptionsStrategy("test_strategy", {})
    
    # For now, using base strategy
    class DummyStrategy(BaseStrategy):
        async def should_enter(self, market_data):
            # Simple dummy strategy - buy every 100th iteration
            if np.random.random() < 0.01:  # 1% chance
                return Order(
                    symbol=market_data['symbol'],
                    quantity=1,
                    price=market_data['price'],
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.BUY
                )
            return None
        
        async def should_exit(self, position, market_data):
            # Exit after 10% profit or 5% loss
            current_price = market_data['price']
            entry_price = position.average_price
            
            profit_pct = (current_price - entry_price) / entry_price
            
            if profit_pct >= 0.10 or profit_pct <= -0.05:
                return Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL
                )
            return None
    
    strategy = DummyStrategy("dummy_strategy")
    
    # Run backtest
    await engine.run_backtest(strategy, "NIFTY_CE")

if __name__ == "__main__":
    asyncio.run(main())