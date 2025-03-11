#!/usr/bin/env python3
"""
Script to convert existing conversation logs to the new format with message boundaries.
"""
import os
import re
from datetime import datetime

def convert_log_file(file_path):
    """Convert a single log file to the new format with message boundaries."""
    # Read the existing log file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regular expression to match the existing log format
    # Matches: [timestamp] sender: message
    pattern = r'\[([\d\-: ]+)\] ([^:]+): (.+?)(?=\n\[|$)'
    
    # Find all messages in the current format
    messages = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
    
    # Create new content with separators
    new_content = []
    separator = "#=====< MESSAGE BOUNDARY >=====# \n"
    
    for match in messages:
        timestamp, sender, message = match.groups()
        # Reconstruct the message with the new separator
        new_content.append(f"{separator}[{timestamp}] {sender}: {message.strip()}\n")

    # Write the converted content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

def main():
    """Find and convert all log files."""
    # Base directory for conversation logs
    base_dir = "logs/conversations"
    
    # Walk through all directories and files
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                print(f"Converting {file_path}...")
                try:
                    convert_log_file(file_path)
                    print(f"Successfully converted {file_path}")
                except Exception as e:
                    print(f"Error converting {file_path}: {str(e)}")

if __name__ == "__main__":
    main()