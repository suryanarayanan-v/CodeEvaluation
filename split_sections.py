import json
import os

def create_sample(file_path, start_line, start_char, end_line, end_char, base_dir="."):
    full_path = os.path.join(base_dir, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found at {full_path}")
        return None
    except Exception as e:
        print(f"Error reading file {full_path}: {e}")
        return None

    start_line_idx = start_line - 1
    end_line_idx = end_line - 1

    # Prefix
    prefix_lines = lines[:start_line_idx]
    if start_line_idx < len(lines):
         prefix_lines.append(lines[start_line_idx][:start_char])
    prefix = "".join(prefix_lines)

    # Suffix
    suffix_lines = []
    if end_line_idx < len(lines):
         suffix_lines.append(lines[end_line_idx][end_char:])
    if end_line_idx + 1 < len(lines):
        suffix_lines.extend(lines[end_line_idx + 1:])
    suffix = "".join(suffix_lines)

    # Middle
    middle_lines = []
    if start_line_idx == end_line_idx:
        if start_line_idx < len(lines):
            middle_lines.append(lines[start_line_idx][start_char:end_char])
    else:
        if start_line_idx < len(lines):
            middle_lines.append(lines[start_line_idx][start_char:])
        middle_lines.extend(lines[start_line_idx + 1 : end_line_idx])
        if end_line_idx < len(lines):
             middle_lines.append(lines[end_line_idx][:end_char])
    middle = "".join(middle_lines)

    # Basic validation
    if not prefix and not suffix and not middle:
        print(f"Warning: Empty result for {file_path} ({start_line}-{end_line}). Check coordinates.")
        return None
    if not middle:
         # Safe if middle part is intended to be empty
         print(f"Warning: Empty middle for {file_path} ({start_line}-{end_line}). Is start >= end?")

    return {
        "file": file_path,
        "prefix": prefix,
        "suffix": suffix,
        "middle": middle,
        "meta": {"lines": f"{start_line}:{start_char}-{end_line}:{end_char}"}
    }

