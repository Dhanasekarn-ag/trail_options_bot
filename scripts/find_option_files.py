# ==================== find_option_files.py ====================
"""
Script to find files that contain option-related code in your bot
Run this to identify which files need to be modified
"""

import os
import re
from pathlib import Path

def find_option_related_files(root_dir="."):
    """Find all files that contain option-related code"""
    
    # Keywords to search for in files
    option_keywords = [
        "option", "strike", "premium", "expiry", "CE", "PE", 
        "call", "put", "NSE_FO", "instrument_key",
        "market-quote", "ltp", "last_price"
    ]
    
    # File extensions to search
    extensions = [".py", ".js", ".ts"]
    
    results = []
    
    print("🔍 Searching for option-related files...")
    print("=" * 60)
    
    for root, dirs, files in os.walk(root_dir):
        # Skip common directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.venv']):
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                        # Check if file contains option-related keywords
                        matches = []
                        for keyword in option_keywords:
                            if keyword.lower() in content:
                                matches.append(keyword)
                        
                        if matches:
                            # Count lines and get more details
                            lines = content.split('\n')
                            line_count = len(lines)
                            
                            # Find specific function names
                            functions = re.findall(r'def\s+(\w*(?:option|strike|premium|expiry)\w*)', content)
                            classes = re.findall(r'class\s+(\w*(?:option|strike|premium|expiry)\w*)', content)
                            
                            results.append({
                                'file': str(file_path),
                                'matches': matches,
                                'functions': functions,
                                'classes': classes,
                                'lines': line_count
                            })
                            
                except Exception as e:
                    pass  # Skip files that can't be read
    
    # Sort by relevance (number of matches)
    results.sort(key=lambda x: len(x['matches']), reverse=True)
    
    print(f"Found {len(results)} files with option-related content:\n")
    
    for i, result in enumerate(results, 1):
        print(f"📁 {i}. {result['file']}")
        print(f"   Keywords: {', '.join(result['matches'][:5])}{'...' if len(result['matches']) > 5 else ''}")
        print(f"   Lines: {result['lines']}")
        
        if result['functions']:
            print(f"   Functions: {', '.join(result['functions'])}")
        if result['classes']:
            print(f"   Classes: {', '.join(result['classes'])}")
        print()
    
    return results

if __name__ == "__main__":
    print("🔧 Option Code Finder")
    print("This will help identify files to modify")
    print("=" * 60)
    
    results = find_option_related_files()
    
    if results:
        print("🎯 PRIORITY FILES TO MODIFY:")
        print("=" * 60)
        
        # Show top 3 most relevant files
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result['file']} - HIGH PRIORITY")
            
        print("\n💡 NEXT STEPS:")
        print("1. Examine these files to understand current option code")
        print("2. Look for functions that fetch option contracts or LTP")
        print("3. Replace with the new OptionDataManager class")
        print("4. Update any calling code to use the new methods")
        
    else:
        print("❌ No option-related files found!")
        print("💡 You may need to create new option handling code")