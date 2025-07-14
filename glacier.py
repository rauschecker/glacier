#!/usr/bin/env python3

import argparse
import sys
import os
import datetime
import time
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

def read_urls_file(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: URLs file not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    if not urls:
        print(f"Warning: No URLs found in {filepath}")
    return urls

def chunk_list(lst, n):
    """Split list `lst` into chunks of size n (last chunk may be smaller)."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main():
    parser = argparse.ArgumentParser(prog="glacier")
    parser.add_argument('-t', '--tech', type=str, help='Describe the tech stack of the application')
    parser.add_argument('-u', '--urls', type=str, help='Path to a file containing known URLs (one per line)')
    parser.add_argument('-k', '--openai-key-file', type=str, help='Path to file containing OpenAI API key (or set env OPENAI_API_KEY)')
    parser.add_argument('-o', '--output', type=str, help='File path to write the results')
    parser.add_argument('-n', '--num-results', type=int, default=10, help='Total number of results to request from OpenAI (default: 10)')
    parser.add_argument('-T', '--max-tokens', type=int, default=1000, help='Max tokens per OpenAI API call (default: 1000)')
    parser.add_argument('-b', '--batch-size', type=int, default=10, help='Number of URLs per batch (default: 10)')
    parser.add_argument('-c', '--cost-estimate', action='store_true', help='Estimate cost before running')
    args = parser.parse_args()

    print(GLACIER_LOGO)

    openai_client = None
    try:
        from openai_client import OpenAIClient
        openai_key = None
        if args.openai_key_file:
            if not os.path.isfile(args.openai_key_file):
                print(f"OpenAI key file not found: {args.openai_key_file}")
                sys.exit(1)
            with open(args.openai_key_file, 'r') as f:
                openai_key = f.read().strip()
        openai_client = OpenAIClient(api_key=openai_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        sys.exit(1)

    urls = []
    if args.urls:
        urls = read_urls_file(args.urls)
        print(f"URLs loaded from {args.urls}: {len(urls)} URLs")

    if not args.tech and not urls:
        print("No tech stack or URLs provided — nothing to analyze.")
        sys.exit(0)

    # Determine batches
    if urls:
        batch_size = max(1, args.batch_size)
        url_batches = list(chunk_list(urls, batch_size))
    else:
        url_batches = [ [] ]  # single batch with no URLs

    total_batches = len(url_batches)

    # Calculate results per batch (split n evenly, rounding up for last batch)
    base_results_per_batch = args.num_results // total_batches
    remainder = args.num_results % total_batches
    results_per_batch_list = [base_results_per_batch + (1 if i < remainder else 0) for i in range(total_batches)]

    # Cost estimate before running (if requested)
    if args.cost_estimate:
        total_tokens = 0
        for i, batch_urls in enumerate(url_batches):
            n_for_batch = results_per_batch_list[i]
            if args.tech and batch_urls:
                prompt = prompt_tech_and_urls(args.tech, batch_urls, n_for_batch)
            elif args.tech and not batch_urls:
                prompt = prompt_tech_only(args.tech, n_for_batch)
            elif not args.tech and batch_urls:
                prompt = prompt_urls_only(batch_urls, n_for_batch)
            else:
                continue
            tokens = openai_client.count_tokens(prompt) + args.max_tokens
            total_tokens += tokens
        cost = openai_client.estimate_cost(total_tokens)
        print(f"Estimated total tokens: {total_tokens}")
        print(f"Estimated total cost (USD): ${cost:.6f}")
        sys.exit(0)

    # Prepare output
    output_path = args.output
    if not output_path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"urls_{timestamp}.txt"

    all_results = set()

    print("Glacier is thinking...")
    try:
        for i, batch_urls in enumerate(tqdm(url_batches, desc="Processing batches", unit="batch")):
            n_for_batch = results_per_batch_list[i]
            if n_for_batch == 0:
                continue

            if args.tech and batch_urls:
                prompt = prompt_tech_and_urls(args.tech, batch_urls, n_for_batch)
            elif args.tech and not batch_urls:
                prompt = prompt_tech_only(args.tech, n_for_batch)
            elif not args.tech and batch_urls:
                prompt = prompt_urls_only(batch_urls, n_for_batch)
            else:
                print("No input data for batch, skipping")
                continue

            response = openai_client.call_openai(prompt, max_tokens=args.max_tokens)
            # Split response lines and add unique URLs
            for line in response.splitlines():
                line = line.strip()
                if line:
                    all_results.add(line)

            # Optional: brief delay to respect rate limits
            time.sleep(1)

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        sys.exit(1)

    if all_results:
        try:
            with open(output_path, 'w') as f:
                for url in sorted(all_results):
                    f.write(url + "\n")
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error writing to output file {output_path}: {e}")
            sys.exit(1)
    else:
        print("No results generated.")

if __name__ == '__main__':
    main()
