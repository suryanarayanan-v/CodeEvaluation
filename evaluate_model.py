# evaluate_model.py
import json
import torch
import transformers
from evaluate import load as load_metric
import argparse
import os
from tqdm import tqdm

def format_prompt(sample, fim_enabled=False, fim_token="<fim_middle>", prefix_token="<fim_prefix>", suffix_token="<fim_suffix>", eos_token="<|endoftext|>"):
    if fim_enabled:
        return f"{prefix_token}{sample['prefix']}{suffix_token}{sample['suffix']}{fim_token}"
    else:
        return sample['prefix']


def run_evaluation(model_id, dataset_path, output_dir, use_fim, hf_token=None, quantization_bits=None, max_new_tokens=128, temperature=0.2, batch_size=1):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_filename = os.path.join(output_dir, f"results_{model_id.replace('/', '_')}.jsonl")
    print(f"Starting evaluation for model: {model_id}")
    print(f"Dataset: {dataset_path}")
    print(f"Outputting results to: {output_filename}")
    print(f"Using FIM prompting: {use_fim}")
    print(f"Quantization: {quantization_bits}-bit" if quantization_bits else "None")
    print(f"Max new tokens: {max_new_tokens}")
    print(f"Temperature: {temperature}")
    print(f"Batch size: {batch_size}")

    print(f"Using HF Token: {'Yes' if hf_token else 'No'}")


    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = [json.loads(line) for line in f]
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    print("Loading model and tokenizer...")
    quantization_config = None
    torch_dtype = torch.float32

    if quantization_bits == 4:
        quantization_config = transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        torch_dtype = torch.bfloat16
        print("Using 4-bit quantization (NF4, bfloat16 compute, double quant)")
    elif quantization_bits == 8:
        quantization_config = transformers.BitsAndBytesConfig(
            load_in_8bit=True,
        )
        print("Using 8-bit quantization")

    try:
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=hf_token,
            padding_side = 'left'
        )
        model = transformers.AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch_dtype,
            trust_remote_code=True,
            token=hf_token
        )
        model.eval()
    except Exception as e:
        print(f"Error loading model/tokenizer: {e}")
        if "authentication" in str(e).lower():
             print("Hint: This might be a gated model. Ensure you have accepted the terms")
             print("on the Hugging Face model page and provided a valid --hf_token.")
        return

    if tokenizer.pad_token is None:
        if tokenizer.eos_token:
            tokenizer.pad_token = tokenizer.eos_token
            print(f"Set pad_token to eos_token: {tokenizer.pad_token}")
        else:
            tokenizer.add_special_tokens({'pad_token': '[PAD]'})
            model.resize_token_embeddings(len(tokenizer))
            print("Added '[PAD]' as pad_token.")

    # These might need adjustment based on specific model documentation
    fim_token = "<fim_middle>"
    prefix_token = "<fim_prefix>"
    suffix_token = "<fim_suffix>"
    eos_token = tokenizer.eos_token if tokenizer.eos_token else "<|endoftext|>"

    if "starcoder" in model_id.lower():
        fim_token = "<fim_middle>"
        prefix_token = "<fim_prefix>"
        suffix_token = "<fim_suffix>"
        # StarCoder uses a different FIM structure and might work better without FIM tokens.
        # use_fim = False
    elif "codellama" in model_id.lower():
        # CodeLlama uses different FIM tokens (check specific model card if needed)
        # prefix_token = "<PRE>"
        # suffix_token = "<SUF>"
        # fim_token = "<MID>"
        # But simple prefix often works well too.
        pass # Keep defaults or adjust if needed based on experimentation/docs

    print("Loading metrics...")
    exact_match = load_metric("exact_match")
    chrf = load_metric("chrf") # chrF++

    results = []
    prompts = [format_prompt(sample, use_fim, fim_token, prefix_token, suffix_token, eos_token) for sample in dataset]
    print(f"Generated {len(prompts)} prompts.")

    print("Starting generation...")
    generated_completions = []

    for i in tqdm(range(0, len(prompts), batch_size), desc="Generating"):
        batch_prompts = prompts[i:min(i + batch_size, len(prompts))]

        inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True, max_length=1024).to(model.device) # Adjust max_length if needed

        with torch.no_grad():
             outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0, # Only sample if temperature > 0
                top_p=0.9 if temperature > 0 else None, # Nucleus sampling
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # Decode only the newly generated tokens for each item in the batch
        batch_completions = tokenizer.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)
        generated_completions.extend(batch_completions)


    print("Generation complete. Calculating metrics...")
    total_em = 0
    total_chrf = 0.0

    with open(output_filename, 'w', encoding='utf-8') as f_out:
        for idx, sample in enumerate(tqdm(dataset, desc="Calculating Metrics")):
            completion = generated_completions[idx]
            middle_true = sample['middle']

            if use_fim and sample['suffix']:
                # try removing the suffix if it appears at the end
                suffix_preview = sample['suffix'].strip().split('\n')[0][:20] # Check start of suffix
                if completion.strip().endswith(suffix_preview):
                    # Simple check, might not always be correct
                    pass

            # Remove potential trailing EOS tokens if they weren't skipped
            if eos_token and completion.endswith(eos_token):
                 completion = completion[:-len(eos_token)]

            completion = completion.strip() # Basic whitespace strip

            # Calculate metrics
            em_result = exact_match.compute(predictions=[completion], references=[middle_true])
            chrf_result = chrf.compute(predictions=[completion], references=[middle_true]) # chrF++

            em_score = em_result['exact_match']
            chrf_score = chrf_result['score']

            total_em += em_score
            total_chrf += chrf_score

            result_entry = {
                "file": sample["file"],
                "meta": sample["meta"],
                "prefix": sample["prefix"],
                "suffix": sample["suffix"],
                "middle_ground_truth": middle_true,
                "generated_completion": completion,
                "exact_match": em_score,
                "chrf": chrf_score, # chrF++ score
                "model_id": model_id,
                "prompt": prompts[idx] # Store the prompt used
            }
            results.append(result_entry)
            f_out.write(json.dumps(result_entry) + '\n')

    num_samples = len(dataset)
    avg_em = total_em / num_samples if num_samples > 0 else 0
    avg_chrf = total_chrf / num_samples if num_samples > 0 else 0

    print("\n--- Evaluation Summary ---")
    print(f"Model: {model_id}")
    print(f"Total Samples: {num_samples}")
    print(f"Average Exact Match: {avg_em:.4f}")
    print(f"Average chrF: {avg_chrf:.4f}") # 0-100 scale
    print("--------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Code Completion Model")
    parser.add_argument("--model_id", type=str, required=True, help="Hugging Face model ID (e.g., 'codellama/CodeLlama-7b-hf')")
    parser.add_argument("--dataset_path", type=str, default="completion_dataset.jsonl", help="Path to the dataset file (.jsonl)")
    parser.add_argument("--output_dir", type=str, default="eval_results", help="Directory to save evaluation results")
    parser.add_argument("--use_fim", action='store_true', help="Use Fill-in-the-Middle prompting format (if supported by model)")
    parser.add_argument("--hf_token", type=str, default=None, help="Your Hugging Face Hub token for accessing gated models.")
    parser.add_argument("--quantization", type=int, choices=[4, 8], default=None, help="Apply 4-bit or 8-bit quantization (requires bitsandbytes)")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="Maximum number of new tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.2, help="Generation temperature (0 for deterministic)")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for generation (adjust based on VRAM)")

    args = parser.parse_args()

    if args.quantization:
        try:
            import bitsandbytes
        except ImportError:
            print("Error: Quantization requires the 'bitsandbytes' library. Please install it (`pip install bitsandbytes`).")
            exit(1)

    run_evaluation(
        model_id=args.model_id,
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        use_fim=args.use_fim,
        hf_token=args.hf_token, # Pass the token from args
        quantization_bits=args.quantization,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        batch_size=args.batch_size
    )
