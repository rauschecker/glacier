#!/usr/bin/env python3

import argparse
import sys
import os
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from openai_client import OpenAIClient, prompt_tech_only, prompt_tech_and_urls, prompt_urls_only

GLACIER_LOGO = r"""
       /\                       _            _    
      /  \    /\           __ _| | __ _  ___(_) ___ _ __  
     /    \  /  \         / _` | |/ _` |/ __| |/ _ \ '__|     
    /      \/    \       | (_| | | (_| | (__| |  __/ |   
   /              \       \__, |_|\__,_|\___|_|\___|_|  
  /________________\      |___/                                v0.0.1
                                    @rauschecker (https://andresr.de)
"""

class GlacierHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = "Usage: "
        return super().add_usage(usage, actions, groups, prefix)

def print_short_usage(parser):
    print(GLACIER_LOGO)
    usage = parser.format_usage()
    print(usage.strip())

def print_help_with_logo(parser):
    print(GLACIER_LOGO)
    parser.print_help()

def read_openai_api_key(filepath=None):
    if filepath:
        if not os.path.isfile(filepath):
            print(f"Error: OpenAI key file not found: {filepath}")
            sys.exit(1)
        with open(filepath, 'r') as f:
            key = f.read().strip()
            if not key:
                print(f"Error: OpenAI key file is empty: {filepath}")
                sys.exit(1)
            return key
    else:
        return None  # fallback to env var in OpenAIClient

def read_urls_file(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: URLs file not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    if not urls:
        print(f"Warning: No URLs found in {filepath}")
    return urls

def read_wordlist_file(filepath):
    if not filepath:
        return set()
    if not os.path.isfile(filepath):
        print(f"Error: Wordlist file not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def batch_urls(urls, max_tokens_per_batch, client, prompt_func, tech):
    """
    Batch URLs so each batch’s prompt + output fits under max_tokens_per_batch.
    """
    batches = []
    current_batch = []

    for url in urls:
        tentative_batch = current_batch + [url]

        # Build prompt for tentative batch
        if tech:
            prompt = prompt_func(tech, tentative_batch, len(tentative_batch))
        else:
            prompt = prompt_func(tentative_batch, len(tentative_batch))

        prompt_tokens = client.count_tokens(prompt)
        # Estimate output tokens: ~20 tokens per result per URL
        estimated_output_tokens = len(tentative_batch) * 20
        total_tokens = prompt_tokens + estimated_output_tokens

        if total_tokens > max_tokens_per_batch:
            if current_batch:
                batches.append(current_batch)
            current_batch = [url]
        else:
            current_batch = tentative_batch

    if current_batch:
        batches.append(current_batch)

    return batches

def main():
    parser = argparse.ArgumentParser(
        prog="glacier",
        formatter_class=GlacierHelpFormatter,
        add_help=False
    )

    parser.add_argument('-t', '--tech', type=str, help='Describe the tech stack of the application')
    parser.add_argument('-u', '--urls', type=str, help='Path to a file containing known URLs (one per line)')
    parser.add_argument('-w', '--wordlist', type=str, help='Path to a file containing relative URLs to exclude from output')
    parser.add_argument('-k', '--openai-key-file', type=str, help='Path to a file containing the OpenAI API key. Alternatively set env var OPENAI_API_KEY.')
    parser.add_argument('-o', '--output', type=str, help='File path to write the results')
    parser.add_argument('-n', '--num-results', type=int, default=10,
                        help='Number of results to request from OpenAI (default: 10)')
    parser.add_argument('-T', '--max-tokens', type=int, default=4000,
                        help='Maximum tokens to use in the OpenAI query (default: 4000)')
    parser.add_argument('-c', '--cost', action='store_true',
                        help='Output token cost and exit')
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')

    if len(sys.argv) == 1:
        print_short_usage(parser)
        sys.exit(0)

    args = parser.parse_args()

    if args.help:
        print_help_with_logo(parser)
        sys.exit(0)

    print(GLACIER_LOGO)

    openai_key = read_openai_api_key(args.openai_key_file)
    openai_client = OpenAIClient(api_key=openai_key)

    urls = read_urls_file(args.urls) if args.urls else []
    wordlist = read_wordlist_file(args.wordlist) if args.wordlist else set()

    if urls:
        print(f"URLs loaded from {args.urls}: {len(urls)} URLs")
    if wordlist:
        print(f"Wordlist loaded from {args.wordlist}: {len(wordlist)} entries")

    if args.cost:
        # Estimate cost for prompt + output tokens
        if urls and args.tech:
            prompt = prompt_tech_and_urls(args.tech, urls, args.num_results)
        elif urls:
            prompt = prompt_urls_only(urls, args.num_results)
        elif args.tech:
            prompt = prompt_tech_only(args.tech, args.num_results)
        else:
            print("Nothing to estimate cost for: no tech or URLs provided.")
            sys.exit(0)

        prompt_tokens = openai_client.count_tokens(prompt)
        output_tokens = args.num_results * 20
        total_tokens = prompt_tokens + output_tokens

        print(f"Estimated total tokens: {total_tokens}")
        sys.exit(0)

    # Determine prompt function based on inputs
    if args.tech and urls:
        prompt_func = prompt_tech_and_urls
    elif args.tech:
        prompt_func = prompt_tech_only
    elif urls:
        prompt_func = prompt_urls_only
    else:
        print("No tech or URLs provided — nothing to analyze.")
        sys.exit(1)

    # Batch URLs by token limits
    batches = batch_urls(urls, args.max_tokens, openai_client, prompt_func, args.tech)
    print(f"Splitting into {len(batches)} batches based on token limits")

    total_results = args.num_results
    num_batches = len(batches)
    base_n = total_results // num_batches
    remainder = total_results % num_batches

    results = []
    errors = 0

    def process_batch(batch_idx, batch_urls):
        n_for_batch = base_n + (1 if batch_idx < remainder else 0)
        if args.tech:
            prompt = prompt_func(args.tech, batch_urls, n_for_batch)
        else:
            prompt = prompt_func(batch_urls, n_for_batch)
        try:
            return openai_client.call_openai(prompt, max_tokens=args.max_tokens)
        except Exception as e:
            return f"ERROR: {e}"

    with ThreadPoolExecutor(max_workers=min(10, num_batches)) as executor:
        futures = {executor.submit(process_batch, i, batch): i for i, batch in enumerate(batches)}
        with tqdm(total=num_batches, desc="Processing batches") as pbar:
            for future in as_completed(futures):
                idx = futures[future]
                result = future.result()
                if result.startswith("ERROR:"):
                    print(f"Error calling OpenAI API on batch {idx + 1}: {result}")
                    errors += 1
                else:
                    results.append(result)
                pbar.update(1)

    # Combine results, deduplicate, filter by wordlist
    all_lines = []
    for r in results:
        all_lines.extend([line.strip() for line in r.splitlines() if line.strip()])

    filtered = []
    seen = set()
    for line in all_lines:
        if line not in seen and line not in wordlist:
            filtered.append(line)
            seen.add(line)

    output_path = args.output if args.output else f"urls_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(output_path, 'w') as f:
            f.write("\n".join(filtered))
        print(f"\nDone. Results saved to: {output_path}")
    except Exception as e:
        print(f"Error writing to output file {output_path}: {e}")

if __name__ == '__main__':
    main()
