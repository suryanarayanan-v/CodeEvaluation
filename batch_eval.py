import subprocess
import os

PYTHON_EXECUTABLE = "python"
EVAL_SCRIPT = "evaluate_model.py"
DATASET_PATH = "completion_dataset.jsonl"
OUTPUT_DIR = "eval_results"
BATCH_SIZE = 2
HF_TOKEN = os.environ['hf_token']

models_with_fim = [
    "bigcode/starcoderbase-1b",
    "deepseek-ai/deepseek-coder-6.7b-base",
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Base",
    "codellama/CodeLlama-7b-hf",
    "codellama/CodeLlama-7b-Instruct-hf",
]

models_without_fim_quant = [
    "codellama/CodeLlama-34b-hf",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",

]

quantization_levels = [None, 4, 8]

os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_command(cmd_list):
    print("-" * 80)
    print(f"Executing: {' '.join(cmd_list)}")
    print("-" * 80)
    try:
        process = subprocess.run(cmd_list, check=True, text=True)
        print(f"Command completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Return code: {e.returncode}")
    except FileNotFoundError:
        print(f"Error: '{cmd_list[0]}' or '{cmd_list[1]}' not found.")
        print("Please ensure Python and the evaluation script are accessible.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    print("-" * 80 + "\n")


print(">>> Starting evaluations for models WITH FIM support <<<")
for model_id in models_with_fim:
    command = [
        PYTHON_EXECUTABLE,
        EVAL_SCRIPT,
        "--model_id", model_id,
        "--dataset_path", DATASET_PATH,
        "--output_dir", OUTPUT_DIR,
        "--batch_size", str(BATCH_SIZE),
        "--use_fim",
    ]
    if HF_TOKEN:
        command.extend(["--hf_token", HF_TOKEN])

    run_command(command)

print("\n>>> Starting evaluations for models WITHOUT FIM (with quantization variants) <<<")
for model_id in models_without_fim_quant:
    for quant_level in quantization_levels:
        command = [
            PYTHON_EXECUTABLE,
            EVAL_SCRIPT,
            "--model_id", model_id,
            "--dataset_path", DATASET_PATH,
            "--output_dir", OUTPUT_DIR,
            "--batch_size", str(BATCH_SIZE),
            # No --use_fim flag here
        ]
        if HF_TOKEN:
            command.extend(["--hf_token", HF_TOKEN])

        if quant_level is not None:
            command.extend(["--quantization", str(quant_level)])
            print(f"   (Quantization: {quant_level}-bit)")
        else:
            print("   (Quantization: None)")


        run_command(command)

print("\n>>> All evaluation runs scheduled <<<")