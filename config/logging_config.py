# ==================== config/logging_config.py (ENHANCED) ====================
import logging
import logging.handlers
from pathlib import Path
from config.settings import get_settings
import logging
import sys
import os

def setup_logging():
    """Setup logging configuration with enhanced emoji handling"""
    settings = get_settings()
    
    # ENHANCED FIX FOR WINDOWS ENCODING ISSUES
    if sys.platform == 'win32':
        try:
            # Method 1: Set environment variables
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # Method 2: Force UTF-8 encoding for Windows console
            import io
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
                
        except Exception as e:
            print(f"Warning: Could not set UTF-8 encoding: {e}")
    
    # Create custom formatter that handles emojis safely
    class EmojiSafeFormatter(logging.Formatter):
        """Custom formatter that converts emojis to text for Windows compatibility"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Emoji to text mappings
            self.emoji_map = {
                '🎯': '[TARGET]',
                '💰': '[MONEY]',
                '📈': '[UP]',
                '🟢': '[GREEN]',
                '📊': '[CHART]',
                '✅': '[OK]',
                '❌': '[ERROR]',
                '🚀': '[SIGNAL]',
                '🛑': '[STOP]',
                '🔍': '[SEARCH]',
                '🔴': '[RED]',
                '🟡': '[YELLOW]',
                '🕯️': '[CANDLE]',
                '⌛': '[WAIT]',
                '⏰': '[TIME]',
                '📉': '[DOWN]',
                '🔥': '[HOT]',
                '📋': '[LIST]',
                '🎉': '[SUCCESS]',
                '💪': '[STRONG]',
                '⚠️': '[WARNING]',
                '🌟': '[STAR]',
                '💵': '[CASH]',
                '📱': '[ALERT]',
                '🏆': '[WIN]',
                '🔔': '[NOTIFY]',
                '💡': '[IDEA]',
                '⭐': '[GOOD]',
                '💯': '[100]',
                '🚨': '[ALARM]',
                '📢': '[NEWS]',
                '🔵': '[BLUE]',
                '🟠': '[ORANGE]',
                '🟣': '[PURPLE]',
                '⚡': '[FAST]',
                '🌈': '[MULTI]',
                '🔋': '[POWER]',
                '⚙️': '[SETTINGS]',
                '🛠️': '[TOOLS]',
                '📝': '[NOTE]',
                '📄': '[DOC]',
                '📂': '[FOLDER]',
                '💼': '[TRADE]',
                '🎲': '[RANDOM]'
            }
        
        def format(self, record):
            # Convert emojis to text before formatting
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                msg = str(record.msg)
                for emoji, text in self.emoji_map.items():
                    msg = msg.replace(emoji, text)
                record.msg = msg
            
            # Handle args that might contain emojis
            if hasattr(record, 'args') and record.args:
                try:
                    clean_args = []
                    for arg in record.args:
                        if isinstance(arg, str):
                            clean_arg = str(arg)
                            for emoji, text in self.emoji_map.items():
                                clean_arg = clean_arg.replace(emoji, text)
                            clean_args.append(clean_arg)
                        else:
                            clean_args.append(arg)
                    record.args = tuple(clean_args)
                except Exception:
                    pass  # If anything goes wrong, just use original args
            
            return super().format(record)
    
    # Create formatters using the emoji-safe formatter
    detailed_formatter = EmojiSafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = EmojiSafeFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Enhanced Console handler with UTF-8 support
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Try to set UTF-8 encoding on the console handler
        if hasattr(console_handler.stream, 'reconfigure'):
            try:
                console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass  # If reconfigure fails, continue with default
                
        root_logger.addHandler(console_handler)
    except Exception as e:
        print(f"Warning: Could not setup console handler: {e}")
    
    # File handler - detailed logs with UTF-8 encoding
    try:
        log_file = settings.logs_dir / "trading_bot.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, 
            encoding='utf-8', errors='replace'  # Added error handling
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file handler: {e}")
    
    # Error file handler with UTF-8 encoding
    try:
        error_file = settings.logs_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3,
            encoding='utf-8', errors='replace'  # Added error handling
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"Warning: Could not setup error handler: {e}")
    
    # Trading file handler - for trades and strategy logs with UTF-8
    try:
        trades_file = settings.logs_dir / "trades.log"
        trades_handler = logging.handlers.RotatingFileHandler(
            trades_file, maxBytes=5*1024*1024, backupCount=10,
            encoding='utf-8', errors='replace'  # Added error handling
        )
        trades_handler.setLevel(logging.INFO)
        trades_handler.setFormatter(detailed_formatter)
        
        # Create trading logger
        trading_logger = logging.getLogger('trading')
        # Clear existing handlers for trading logger
        for handler in trading_logger.handlers[:]:
            trading_logger.removeHandler(handler)
        trading_logger.addHandler(trades_handler)
        trading_logger.setLevel(logging.INFO)
        trading_logger.propagate = False  # Prevent duplicate logs
    except Exception as e:
        print(f"Warning: Could not setup trading handler: {e}")
    
    # Suppress noisy loggers
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Test the logging setup
    try:
        test_logger = logging.getLogger(__name__)
        test_logger.info("Logging system initialized with emoji safety")
        test_logger.info(f"Log files location: {settings.logs_dir}")
    except Exception as e:
        print(f"Warning: Logging test failed: {e}")

# Enhanced UTF-8 Stream Handler
class UTF8StreamHandler(logging.StreamHandler):
    """Enhanced stream handler with better UTF-8 support"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        if stream is None:
            stream = sys.stdout
            
        # Try multiple methods to ensure UTF-8 encoding
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
        
        # Set the stream
        self.stream = stream
    
    def emit(self, record):
        """Emit a record with emoji safety"""
        try:
            msg = self.format(record)
            # Ensure the message can be encoded
            if isinstance(msg, str):
                # Try to encode and decode to catch any encoding issues
                try:
                    msg.encode('utf-8')
                except UnicodeEncodeError:
                    # If encoding fails, replace problematic characters
                    msg = msg.encode('utf-8', errors='replace').decode('utf-8')
            
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Legacy function for backward compatibility
def setup_utf8_logging():
    """Setup UTF-8 logging to handle emojis properly - Enhanced version"""
    
    # Remove existing handlers
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Add UTF-8 compatible handlers with emoji safety
    try:
        file_handler = logging.FileHandler(
            logs_dir / 'trading_bot.log', 
            encoding='utf-8', 
            errors='replace'
        )
        console_handler = UTF8StreamHandler(sys.stdout)
        
        # Create emoji-safe formatter
        class SafeFormatter(logging.Formatter):
            def format(self, record):
                # Replace emojis with text
                if hasattr(record, 'msg') and isinstance(record.msg, str):
                    msg = str(record.msg)
                    emoji_replacements = {
                        '🎯': '[TARGET]', '💰': '[MONEY]', '📈': '[UP]',
                        '🟢': '[GREEN]', '📊': '[CHART]', '✅': '[OK]',
                        '❌': '[ERROR]', '🚀': '[SIGNAL]', '🛑': '[STOP]'
                    }
                    for emoji, text in emoji_replacements.items():
                        msg = msg.replace(emoji, text)
                    record.msg = msg
                return super().format(record)
        
        # Set format
        formatter = SafeFormatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Enhanced UTF-8 logging setup completed")
        
    except Exception as e:
        print(f"Error setting up enhanced UTF-8 logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )