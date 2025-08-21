# ==================== quick_fix_emojis.py ====================
"""
Quick fix script to replace emojis with text in your strategy files
Run this script to fix the immediate Unicode error
"""

import os
import re
from pathlib import Path

def fix_emojis_in_file(file_path):
    """Replace emojis with text equivalents in a Python file"""
    
    # Define emoji replacements
    emoji_replacements = {
        '🎯': '[TARGET]',
        '💰': '[MONEY]', 
        '📈': '[UP]',
        '🟢': '[GREEN]',
        '📊': '[CHART]',
        '✅': '[SUCCESS]',
        '❌': '[ERROR]',
        '🚀': '[ROCKET]',
        '🛑': '[STOP]',
        '🔍': '[SEARCH]',
        '🔴': '[RED]',
        '🟡': '[YELLOW]',
        '🕯️': '[CANDLE]',
        '⌛': '[WAIT]',
        '⏰': '[TIME]',
        '📉': '[DOWN]',
        '🔥': '[FIRE]',
        '📋': '[LIST]',
        '🎉': '[CELEBRATE]',
        '💪': '[STRONG]',
        '⚠️': '[WARNING]',
        '🌟': '[STAR]',
        '🔢': '[NUMBERS]',
        '📺': '[SCREEN]',
        '👋': '[WAVE]',
        '💵': '[CASH]',
        '📱': '[PHONE]',
        '🔔': '[BELL]',
        '🎁': '[GIFT]',
        '🏆': '[TROPHY]',
        '📈': '[TREND_UP]',
        '📉': '[TREND_DOWN]',
        '📊': '[STATS]',
        '💡': '[IDEA]',
        '⭐': '[STAR2]',
        '🔥': '[HOT]',
        '💯': '[100]',
        '🚨': '[ALERT]',
        '📢': '[ANNOUNCE]',
        '🎯': '[BULL_EYE]',
        '🔵': '[BLUE]',
        '🟠': '[ORANGE]',
        '🟣': '[PURPLE]',
        '⚡': '[LIGHTNING]',
        '🌈': '[RAINBOW]',
        '🔋': '[BATTERY]',
        '⚙️': '[GEAR]',
        '🛠️': '[TOOLS]',
        '📝': '[NOTE]',
        '📄': '[PAGE]',
        '📂': '[FOLDER]',
        '💼': '[BRIEFCASE]',
        '🎲': '[DICE]'
    }
    
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if any changes were made
        original_content = content
        changes_made = False
        
        # Replace emojis with text equivalents
        for emoji, replacement in emoji_replacements.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                changes_made = True
                print(f"   Replaced '{emoji}' with '{replacement}' in {file_path.name}")
        
        # Write back the file if changes were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed emojis in: {file_path}")
            return True
        else:
            print(f"- No emojis found in: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix emojis in strategy files"""
    print("🔧 Quick Emoji Fix Script")
    print("=" * 50)
    
    # Find Python files in src/strategy directory
    strategy_dir = Path("src/strategy")
    
    if not strategy_dir.exists():
        print(f"✗ Strategy directory not found: {strategy_dir}")
        return
    
    python_files = list(strategy_dir.glob("*.py"))
    
    if not python_files:
        print(f"✗ No Python files found in: {strategy_dir}")
        return
    
    print(f"Found {len(python_files)} Python files to check:")
    
    fixed_files = 0
    for py_file in python_files:
        print(f"\nChecking: {py_file.name}")
        if fix_emojis_in_file(py_file):
            fixed_files += 1
    
    print("\n" + "=" * 50)
    print(f"✓ Fixed emojis in {fixed_files} files")
    print("✓ Your bot should now run without Unicode errors!")
    print("\n💡 Next steps:")
    print("1. Run your bot again: python main.py")
    print("2. Check that logging works without errors")
    print("3. If you still see Unicode errors, update logging_config.py")

if __name__ == "__main__":
    main()