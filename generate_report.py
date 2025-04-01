import json
import os
import argparse
from collections import defaultdict
import textwrap # Keep just in case, but not actively used here

# Number of lines of context to show before and after the change
CONTEXT_LINES = 3
# Indentation string for code blocks within list items
CODE_BLOCK_INDENT = " " * 4

def get_language(filename):
    """Guesses the language for Markdown code blocks based on extension."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext == '.js':
        return 'javascript'
    elif ext == '.cpp' or ext == '.cxx' or ext == '.cc' or ext == '.hpp':
        return 'cpp'
    elif ext == '.py':
        return 'python'
    elif ext == '.java':
        return 'java'
    elif ext == '.md':
        return 'markdown'
    else:
        return ''

def get_context_lines(text, num_lines, from_end=False):
    """Extracts a specified number of lines from the start or end of a text block."""
    lines = text.splitlines()
    if not lines:
        return ""
    if from_end:
        start_index = max(0, len(lines) - num_lines)
        selected_lines = lines[start_index:]
    else:
        end_index = min(num_lines, len(lines))
        selected_lines = lines[:end_index]
    return selected_lines # Return list

def indent_lines(lines, indent_string):
    """Indents each line in a list of strings."""
    if not isinstance(lines, list): # Ensure input is a list
        lines = str(lines).splitlines()
    if not lines:
        return []
    return [indent_string + line for line in lines]

def generate_review_markdown(input_filename, output_filename):
    """Generates the Markdown review report."""
    changes_by_file = defaultdict(list)

    # --- 1. Read and process all changes ---
    try:
        with open(input_filename, 'r', encoding='utf-8') as infile:
            for i, line in enumerate(infile):
                try:
                    change = json.loads(line.strip())
                    # *** UPDATED KEY CHECK (added chrf) ***
                    required_keys = ['file', 'prefix', 'suffix', 'meta',
                                     'generated_completion', 'middle_ground_truth', 'chrf']
                    if not all(k in change for k in required_keys):
                         print(f"Warning: Skipping line {i+1} due to missing required keys ({required_keys}). Found: {list(change.keys())}")
                         continue
                    change['original_line_num'] = i
                    changes_by_file[change['file']].append(change)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON on line {i+1}.")
                except Exception as e:
                    print(f"Warning: Error processing line {i+1}: {e}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    if not changes_by_file:
        print("No valid changes found in the input file.")
        return

    sorted_files = sorted(changes_by_file.keys())

    # --- 2. Write the Markdown report ---
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            # --- Report Header ---
            outfile.write("# Evaluation Report\n\n") # Changed Title
            outfile.write(f"**Source File:** `{input_filename}`\n")
            outfile.write("**Project:** [Your Project Name]\n")
            outfile.write("**Date:** [Current Date]\n")
            outfile.write("**Reviewer:** [Your Name]\n")
            outfile.write("**Overall Status:** [Pending / Approved / Requires Changes]\n\n")
            outfile.write("---\n\n")

            # --- Iterate through sorted files ---
            file_counter = 0
            for file_path in sorted_files:
                file_counter += 1
                changes = changes_by_file[file_path]
                print(f"Processing file: {file_path} ({len(changes)} evaluations)") # Changed terminology
                lang = get_language(file_path)

                outfile.write(f"## File {file_counter}: `{file_path}`\n\n")
                # Removed File Summary and Status
                # outfile.write("**File Summary:** [Overall comments about the changes in this file]\n")
                # outfile.write("**File Status:** [Approved / Requires Changes]\n\n")
                outfile.write("---\n\n")

                # --- Iterate through evaluations in the file ---
                for eval_index, change in enumerate(changes, 1): # Changed variable name
                    prefix = change['prefix']
                    generated_middle = change['generated_completion']
                    ground_truth_middle = change['middle_ground_truth']
                    suffix = change['suffix']
                    lines_info = change['meta'].get('lines', 'N/A')
                    model_id = change.get('model_id', 'N/A')
                    exact_match = change.get('exact_match', 'N/A')
                    chrf_score = change.get('chrf', 'N/A') # Get CHRF score

                    prefix_context_lines = get_context_lines(prefix, CONTEXT_LINES, from_end=True)
                    suffix_context_lines = get_context_lines(suffix, CONTEXT_LINES, from_end=False)
                    generated_middle_lines = generated_middle.splitlines()
                    ground_truth_middle_lines = ground_truth_middle.splitlines()

                    # *** UPDATED Heading: Uses location info ***
                    outfile.write(f"### Evaluation Block {eval_index} (Lines `{lines_info}`)\n\n")

                    # *** REMOVED Location item ***
                    # outfile.write(f"*   **Location:** Lines `{lines_info}`\n")
                    outfile.write(f"*   **Model:** `{model_id}`\n")
                    outfile.write(f"*   **Exact Match Score:** `{exact_match}`\n")

                    # *** ADDED CHRF Score Formatting ***
                    formatted_chrf = "N/A"
                    if isinstance(chrf_score, (int, float)):
                        formatted_chrf = f"{chrf_score:.2f}" # Format to 2 decimal places
                    elif chrf_score != 'N/A': # Check if it's not the string 'N/A'
                         formatted_chrf = str(chrf_score) # Keep other non-numeric values as strings
                    outfile.write(f"*   **CHRF Score:** `{formatted_chrf}`\n\n") # Added newline

                    # --- Helper to write an indented code block ---
                    def write_code_block(header_text, content_lines_list):
                        outfile.write(f"*   **{header_text}**\n\n") # List item text + blank line
                        outfile.write(f"{CODE_BLOCK_INDENT}```{lang}\n") # Indented opening fence
                        for line in indent_lines(content_lines_list, CODE_BLOCK_INDENT): # Indent content SAME as fence
                             outfile.write(f"{line}\n")
                        outfile.write(f"{CODE_BLOCK_INDENT}```\n\n") # Indented closing fence

                    # --- Before Snippet ---
                    before_content = []
                    before_content.extend(prefix_context_lines)
                    before_content.append(f"# --- Target boundary ({lines_info}) ---") # Changed comment
                    before_content.extend(suffix_context_lines)
                    write_code_block("Context (Before Target Location):", before_content) # Changed header text

                    # --- After Snippet (Generated) ---
                    after_content = []
                    after_content.extend(prefix_context_lines)
                    after_content.append(f"# --- Start generated block ({lines_info}) ---")
                    after_content.extend(generated_middle_lines)
                    after_content.append(f"# --- End generated block ---")
                    after_content.extend(suffix_context_lines)
                    write_code_block("Context + Generated Code:", after_content) # Changed header text

                    # --- Ground Truth Snippet ---
                    write_code_block("Ground Truth Code (for reference):", ground_truth_middle_lines) # Changed header text


                    # --- Review Comments Section ---
                    outfile.write(f"*   **Review Comments:**\n")
                    # *** REMOVED Purpose item ***
                    # outfile.write(f"    *   **Purpose:** [What was the goal of this change?]\n")
                    outfile.write(f"    *   **Generated Code Correctness:** [Is the *generated* code correct? Does it meet the purpose? Any bugs?]\n")
                    outfile.write(f"    *   **Comparison to Ground Truth:** [How does the generated code compare to the expected ground truth?]\n")
                    outfile.write(f"    *   **Style/Readability:** [Is the generated code readable and does it follow style guides?]\n")
                    outfile.write(f"    *   **Suggestions/Concerns:** [Any improvements or issues with the generated code?]\n")
                    outfile.write(f"    *   **Verdict:** [Pass / Fail / Needs Minor Fix / Needs Major Fix]\n\n") # Changed Verdict options
                    outfile.write("---\n\n")

            outfile.write("**End of Report**\n")
        print(f"\nReview report successfully generated: '{output_filename}'")

    except Exception as e:
        print(f"Error writing output file '{output_filename}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Markdown code evaluation report from JSON Lines data.") # Changed description
    parser.add_argument("input_file", help="Path to the input file containing JSON objects (one per line).")
    parser.add_argument("-o", "--output", default="evaluation_report.md", help="Path to the output Markdown file (default: evaluation_report.md).") # Changed default name
    parser.add_argument("-c", "--context", type=int, default=3, help=f"Number of context lines to show before/after target location (default: 3).") # Changed help text

    args = parser.parse_args()
    CONTEXT_LINES = args.context

    generate_review_markdown(args.input_file, args.output)