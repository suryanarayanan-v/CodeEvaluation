# Code Completion LLM Evaluation

This project evaluates the performance of various Large Language Models (LLMs) on code completion tasks, specifically focusing on Fill-in-the-Middle (FIM). The evaluation uses a custom dataset containing JavaScript (Node.js/Express) and C++ examples, developed as a solo project.

## Overview

This project evaluates the performance of various Large Language Models (LLMs) on code completion tasks, specifically focusing on Fill-in-the-Middle (FIM). The evaluation uses a custom dataset containing JavaScript (Node.js/Express) and C++ examples, developed as a solo project. **This dataset (`completion_dataset.jsonl`) was generated using the `split_sections.py` script, which partitions specified sections of the source code files into prefix, middle (the target completion), and suffix segments based on manually defined line/character coordinates.**

The primary goal was to assess how well different LLMs could generate missing code segments within existing files. I tested models with FIM capabilities and compared their outputs against ground truth using Exact Match and CHRF metrics.

The dataset includes code from two distinct projects:
*   **JavaScript (Node.js/Express):** Sourced from my implementation of the backend for the blog list application, part of the **University of Helsinki's Full Stack Open course**. This represents a common web development scenario with REST API interactions, database operations (Mongoose), and typical backend logic, chosen for its relatively standard structure and moderate complexity.
*   **C++:** Based on a project from my university coursework focused on solving a **minimum graph cut problem using branch and bound with parallel programming (OpenMP)**. This was selected to challenge the LLMs with more complex algorithmic logic, intricate data structures (`std::vector`, `std::pair`), and parallel execution constructs, requiring a deeper understanding of the code's flow.

A detailed evaluation report for the best-performing model (Deepseek-Coder) is available in [`review.md`](review.md) in the root directory. **Note:** While the *structural template* for `review.md` was generated with the assistance of an LLM (using the `generate_report.py` script), all analytical comments, conclusions, and verdicts within the report are my own original thoughts and assessments. The results `.jsonl` files for all tested models are also available in the `eval_results/` directory.

## Key Findings & Highlights

*   **Best Performing Model:** `deepseek-ai/deepseek-coder-6.7b-base` provided the most accurate and consistent results among the models I tested, particularly for the JavaScript Full Stack Open project code.
*   **JavaScript Performance:**
    *   `deepseek-ai/deepseek-coder-6.7b-base`: Most JavaScript examples from the blog list backend were generated near-perfectly, achieving an average CHRF score around 80. Minor variations (like object key order) slightly reduced scores but didn't impact functional correctness. This suggests good performance on typical web backend patterns.
    *   `bigcode/starcoderbase-1b`: This smaller model achieved an average CHRF score of around 50 for JavaScript. This lower performance aligns with expectations given its significantly smaller size (1B parameters) compared to the ~7B parameter models like Deepseek and CodeLlama.
*   **C++ Performance:** The C++ graph cut code proved significantly more challenging for all tested models, especially with the complex branch and bound logic and parallel constructs. Results were often nonsensical or completely wrong. I suspect potential issues with:
    *   Confusion between C++ template brackets (`<`, `>`) and FIM tokens.
    *   The intricate logic and potentially larger context required exceeding the model's effective capabilities.
*   **Metric Usefulness:**
    *   **Exact Match:** I found this metric to be overly strict and often misleading, especially when minor, non-functional differences (like whitespace or comment changes) exist.
    *   **CHRF (chrF++):** A much better indicator of similarity. Based on my analysis, scores generally interpreted as:
        *   **80-100:** Very good, likely functionally correct or near-identical.
        *   **60-80:** Structure might be okay, but correctness depends heavily on *what* differs. Could indicate minor mistakes (e.g., wrong variable name like `password` vs `passwordHash`) or significant differences in variable content (like log messages, error strings). Requires manual inspection.
        *   **< 50:** Either the generated code is mostly variable content (e.g., long error messages that differ) or the code structure/logic is largely incorrect (as seen with `starcoderbase-1b` on JS and most models on C++).
*   **FIM Token Handling:**
    *   `deepseek-ai/deepseek-coder-6.7b-base`: Used `<｜fim begin｜>`, `<｜fim hole｜>`, `<｜fim end｜>` tokens successfully.
    *   `bigcode/starcoderbase-1b`: Used `<fim_prefix>`, `<fim_suffix>`, `<fim_middle>` tokens as per its standard.
    *   `codellama/CodeLlama-7b-hf`: The standard `<PRE>`, `<MID>`, `<SUF>` tokens did not function correctly with the evaluation script's infilling approach.
*   **Dataset Nuances:**
    *   `blogs.js` included partial starting tokens in the prefix to guide the LLM, while `users.js` used whole words. This difference didn't seem to significantly confuse the better-performing models like Deepseek.
*   **Context Limitation & IDE Integration Opportunities:**
    *   Some errors highlight the need for broader context beyond the immediate prefix/suffix. Current limitations led to issues like choosing incorrect Mongoose methods (`blogs.js`) or generating overly generic error handling (`middleware.js`).
    *   **Future Enhancement:** Minor errors (e.g., incorrect function arguments in `users.js` Block 3) could potentially be caught by sophisticated IDE analysis. More significantly, leveraging features like **IntelliJ's "Go To Definition"** to automatically fetch function signatures/definitions and inject them into the LLM's context could drastically improve accuracy, especially for function calls and API usage, by providing explicit knowledge of expected arguments and types. This would be a powerful way to bridge the gap between the LLM's general knowledge and the specific codebase structure.

## Models Evaluated

*   `bigcode/starcoderbase-1b`
*   `deepseek-ai/deepseek-coder-6.7b-base`
*   `codellama/CodeLlama-7b-hf`
*   `codellama/CodeLlama-7b-Instruct-hf`

## Setup

1.  **Create a Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # Linux/macOS
    # or
    .\.venv\Scripts\activate # Windows
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: For quantization (`--quantization` flag), `bitsandbytes` is required.*

3.  **Set Hugging Face Token (if needed for gated models):**
    ```bash
    export hf_token="your_huggingface_token"
    ```

## Running Evaluations

1.  **Default Batch Evaluation:**
    *   Modify the `models_with_fim` or `models_without_fim_quant` lists in `batch_eval.py` with the Hugging Face model IDs you want to test.
    *   Run the script:
        ```bash
        python batch_eval.py
        ```

2.  **Single Model Evaluation:**
    *   Use the `evaluate_model.py` script directly.
    *   Example:
        ```bash
        python evaluate_model.py \
            --model_id "deepseek-ai/deepseek-coder-6.7b-base" \
            --dataset_path "completion_dataset.jsonl" \
            --output_dir "eval_results" \
            --batch_size 2 \
            --hf_token "your_huggingface_token" \
            --use_fim \
            # --quantization 4 # Optional: Add for 4-bit quantization
            # --max_new_tokens 128 # Optional: Adjust as needed
            # --temperature 0.2 # Optional: Adjust as needed
        ```
    *   `--use_fim`: Enables Fill-in-the-Middle prompting (ensure the model supports it and the script has the correct tokens configured). Omit this flag for standard causal completion.
    *   `--quantization`: Use 4 or 8 for quantization (requires `bitsandbytes`). Use only when there is a lack of VRAM as it will degrade perfomance. 
    *   `--batch_size`: Adjust based on your available VRAM.

## Generating Report Structure

The structural template for the detailed markdown report (`review.md`) can be generated from the `.jsonl` result files using the `generate_report.py` script (which itself leveraged an LLM for its creation). Remember that the *analysis and verdicts* within the final report need to be your own.

```bash
# Example: Generate a report structure from Deepseek results
python generate_report.py eval_results/results_deepseek-ai_deepseek-coder-6.7b-base.jsonl -o report_structure_template.md -c 5
