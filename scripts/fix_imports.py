# ==================== fix_imports.py ====================
"""
Script to automatically fix import statements
Changes all references from upstox_client to upstox_api_client
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if any changes were made
        original_content = content
        
        # Pattern 1: from src.upstox_client import UpstoxClient
        content = re.sub(
            r'from src\.upstox_client import UpstoxClient',
            'from src.upstox_api_client import UpstoxClient',
            content
        )
        
        # Pattern 2: from upstox_client import UpstoxClient
        content = re.sub(
            r'from upstox_client import UpstoxClient',
            'from upstox_api_client import UpstoxClient',
            content
        )
        
        # Pattern 3: import src.upstox_client
        content = re.sub(
            r'import src\.upstox_client',
            'import src.upstox_api_client',
            content
        )
        
        # Pattern 4: Any other variations
        content = re.sub(
            r'upstox_client\.UpstoxClient',
            'upstox_api_client.UpstoxClient',
            content
        )
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in: {file_path}")
            return True
        else:
            print(f"ℹ️ No imports to fix in: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix imports in all Python files"""
    print("🔧 Fixing Import Statements")
    print("=" * 50)
    
    # Files that likely need import fixes
    files_to_check = [
        "src/trading_bot.py",
        "main.py",
        "src/strategy/option_integrated_pine_script.py",
        "src/strategy/enhanced_pine_script_strategy.py",
        "test_option_integration.py",
        "verify_integration.py"
    ]
    
    fixed_count = 0
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            if fix_imports_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Fixed imports in {fixed_count} files")
    print(f"🎯 Your bot is ready to run!")
    
    if fixed_count > 0:
        print(f"\n🚀 Next step: Run your main bot:")
        print(f"python main.py")

if __name__ == "__main__":
    main()