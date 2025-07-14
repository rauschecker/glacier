#!/usr/bin/env python3

import argparse
import sys
import os
import datetime
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

def main():
    parser = argparse.ArgumentParser(
        prog="glacier",
        formatter_class=GlacierHelpFormatter,
        add_help=False
    )

    parser.add_argument('-t', '--tech', type=str, help='Describe the tech stack of the application')
    parser.add_argument('-u', '--urls', type=str, help='Path to a file containing known URLs (one per line)')
    parser.add_argument('-k', '--openai-key-file', type=str, help='Path to a file containing the OpenAI API key.' \
    ' Alternatively set env var OPENAI_API_KEY.')
    parser.add_argument('-o', '--output', type=str, help='File path to write the results')
    parser.add_argument('-n', '--num-results', type=int, default=10,
                        help='Number of results to request from OpenAI (default: 10)')
    parser.add_argument('-T', '--max-tokens', type=int, default=5000,
                        help='Maximum tokens to use in the OpenAI query (default: 5000)')
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

    urls = []
    if args.urls:
        urls = read_urls_file(args.urls)

    if urls:
        print(f"URLs loaded from {args.urls}:")
        for url in urls:
            print(f"  - {url}")

    # Select prompt based on inputs
    prompt = None
    if args.tech and not urls:
        prompt = prompt_tech_only(args.tech, args.num_results)
    elif args.tech and urls:
        prompt = prompt_tech_and_urls(args.tech, urls, args.num_results)
    elif not args.tech and urls:
        prompt = prompt_urls_only(urls, args.num_results)

    if prompt:
        print("Glacier is thinking...")
        response = openai_client.call_openai(prompt, max_tokens=args.max_tokens)
        print("\nDone.:")

        # Determine output file path
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"urls_{timestamp}.txt"

        try:
            with open(output_path, 'w') as f:
                f.write(response)
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error writing to output file {output_path}: {e}")
    else:
        print("No tech or URLs provided — nothing to analyze.")

if __name__ == '__main__':
    main()
