# ==================== Quick Fix Script ====================
# Create this as fix_type_hints.py and run it:

import re
import os

def fix_type_hints_in_file(file_path):
    """Fix common type hint issues in a Python file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: config: Dict = None → config: Optional[Dict] = None
    content = re.sub(
        r'config: Dict = None',
        'config: Optional[Dict] = None',
        content
    )
    
    # Fix 2: Add Optional import if not present
    if 'from typing import' in content and 'Optional' not in content:
        content = re.sub(
            r'from typing import ([^Optional\n]*)',
            r'from typing import \1, Optional',
            content
        )
    
    # Fix 3: Add typing import if completely missing
    if 'from typing import' not in content and 'Optional[Dict]' in content:
        # Add import at the top after other imports
        import_line = 'from typing import Dict, List, Optional, Tuple\n'
        lines = content.split('\n')
        
        # Find where to insert (after other imports)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                insert_index = i + 1
            elif line.strip() == '' and insert_index > 0:
                break
        
        lines.insert(insert_index, import_line)
        content = '\n'.join(lines)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed type hints in {file_path}")

# Files to fix
files_to_fix = [
    'src/strategy/base_strategy.py',
    'src/strategy/complete_pine_script_strategy.py',
    'src/strategy/enhanced_pine_script_strategy.py',
    'src/strategy/option_integrated_pine_script.py',
    'src/options/option_chain_manager.py',
    'src/options/greeks_calculator.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        fix_type_hints_in_file(file_path)
    else:
        print(f"⚠️  File not found: {file_path}")

print("🎉 All type hints fixed!")