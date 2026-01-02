#!/usr/bin/env python3
"""
Script to add Lahiri Ayanamsa settings to all files using Swiss Ephemeris sidereal calculations
"""

import os
import re
import glob

def add_ayanamsa_to_file(filepath):
    """Add Ayanamsa setting to a file if it uses calc_ut with FLG_SIDEREAL"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file uses calc_ut with FLG_SIDEREAL
        if 'calc_ut' not in content or 'FLG_SIDEREAL' not in content:
            return False
        
        # Check if already has set_sid_mode
        if 'set_sid_mode' in content:
            return False
        
        # Check if it imports swisseph
        if 'import swisseph' not in content and 'from swisseph' not in content:
            return False
        
        print(f"Processing: {filepath}")
        
        # Find the first calc_ut call with FLG_SIDEREAL
        pattern = r'(\s*)(.*?swe\.calc_ut\([^)]*FLG_SIDEREAL[^)]*\))'
        matches = list(re.finditer(pattern, content))
        
        if not matches:
            return False
        
        # Add Ayanamsa setting before the first calc_ut call
        first_match = matches[0]
        indent = first_match.group(1)
        
        # Insert Ayanamsa setting with proper indentation
        ayanamsa_line = f"{indent}# Set Lahiri Ayanamsa for accurate Vedic calculations\n{indent}swe.set_sid_mode(swe.SIDM_LAHIRI)\n"
        
        # Insert before the first calc_ut call
        new_content = content[:first_match.start()] + ayanamsa_line + content[first_match.start():]
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ Added Ayanamsa setting to {filepath}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all Python files"""
    backend_dir = "/Users/tarunydv/Desktop/Code/AstrologyApp/backend"
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(backend_dir):
        # Skip certain directories
        skip_dirs = ['__pycache__', '.git', 'logs', 'ephe']
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    processed_count = 0
    for filepath in python_files:
        if add_ayanamsa_to_file(filepath):
            processed_count += 1
    
    print(f"\n✅ Processed {processed_count} files successfully")
    print("All Swiss Ephemeris calculations now use Lahiri Ayanamsa for consistency!")

if __name__ == "__main__":
    main()