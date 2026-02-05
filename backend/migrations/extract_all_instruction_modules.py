#!/usr/bin/env python3
"""
Extract ALL sections from VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION and store as modules
This preserves 100% of the original instruction - admin can enable/disable modules
"""

import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat.chat_context_builder import ChatContextBuilder

def extract_all_modules():
    """Extract all sections from the original instruction"""
    
    instruction = ChatContextBuilder.VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION
    
    db_path = os.getenv('DATABASE_PATH', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM prompt_instruction_modules")
    
    # Split instruction into logical modules based on ## headers
    import re
    
    # Find all major sections (## headers)
    pattern = r'(##+ [^\n]+\n(?:(?!##+ ).)*)'
    sections = re.findall(pattern, instruction, re.DOTALL)
    
    # Also capture the preamble (before first ##)
    preamble_match = re.match(r'^(.*?)(?=##)', instruction, re.DOTALL)
    
    modules = []
    
    # Add preamble as 'core_preamble' module
    if preamble_match:
        preamble = preamble_match.group(1).strip()
        if preamble:
            modules.append({
                'key': 'core_preamble',
                'name': 'Core Preamble',
                'content': preamble,
                'priority': 1
            })
    
    # Process each section
    priority = 10
    for section in sections:
        # Extract section title
        title_match = re.match(r'##+ ([^\n]+)', section)
        if not title_match:
            continue
            
        title = title_match.group(1).strip()
        
        # Generate module key from title
        key = re.sub(r'[^a-z0-9]+', '_', title.lower())
        key = re.sub(r'^_+|_+$', '', key)  # Remove leading/trailing underscores
        key = key[:50]  # Limit length
        
        # Skip if empty
        content = section.strip()
        if not content or len(content) < 50:
            continue
        
        modules.append({
            'key': key,
            'name': title[:100],  # Limit name length
            'content': content,
            'priority': priority
        })
        priority += 10
    
    # Insert all modules
    for module in modules:
        try:
            cursor.execute("""
                INSERT INTO prompt_instruction_modules 
                (module_key, module_name, instruction_text, character_count, is_active, priority)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (
                module['key'],
                module['name'],
                module['content'],
                len(module['content']),
                module['priority']
            ))
        except sqlite3.IntegrityError as e:
            print(f"⚠️  Skipping duplicate key: {module['key']}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ Extracted and stored {len(modules)} instruction modules")
    print(f"\nModules created:")
    total_chars = 0
    for i, module in enumerate(modules, 1):
        chars = len(module['content'])
        total_chars += chars
        print(f"   {i}. {module['key']}: {chars} chars - {module['name'][:60]}")
    
    print(f"\n📊 Total: {total_chars:,} characters")
    print(f"📊 Original: {len(instruction):,} characters")
    print(f"📊 Coverage: {(total_chars/len(instruction)*100):.1f}%")

if __name__ == "__main__":
    extract_all_modules()
