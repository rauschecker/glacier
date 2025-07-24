# glacier

           /\                       _            _    
          /  \    /\           __ _| | __ _  ___(_) ___ _ __  
         /    \  /  \         / _` | |/ _` |/ __| |/ _ \ '__|     
        /      \/    \       | (_| | | (_| | (__| |  __/ |   
       /              \       \__, |_|\__,_|\___|_|\___|_|  
      /________________\      |___/                                v0.0.1
                                        @rauschecker (https://andresr.de)


AI powered pentesting tool

# Installation Instructions
  - generate a new venv:
  
        python -m venv --prompt glacier .venv  && source .venv/bin/activate
  - install python dependencies
  
        pip install -r requirements.txt


# Usage
    glacier [-t TECH] [-u URLS] [-w WORDLIST] [-k OPENAI_KEY_FILE] [-o OUTPUT] [-n NUM_RESULTS] [-T MAX_TOKENS] [-c] [-h]

           options:
             -t, --tech TECH       Describe the tech stack of the application
             -u, --urls URLS       Path to a file containing known URLs (one per line)
             -w, --wordlist WORDLIST
                                   Path to a file containing relative URLs to exclude from output
             -k, --openai-key-file OPENAI_KEY_FILE
                                   Path to a file containing the OpenAI API key. Alternatively set env var OPENAI_API_KEY.
             -o, --output OUTPUT   File path to write the results
             -n, --num-results NUM_RESULTS
                                   Number of results to request from OpenAI (default: 10)
             -T, --max-tokens MAX_TOKENS
                                   Maximum tokens to use in the OpenAI query (default: 4000)
             -c, --cost            Output token cost and exit
             -h, --help            Show this help message and exit


# Disclaimer & Responsible Use Policy

**This tool is intended strictly for authorized security testing, research, and educational purposes only.**

- You **MUST have explicit permission** from the owner of any target system before using this tool against it.
- Unauthorized use against systems you do **not** own or have **no permission** to test is **illegal**, unethical, and strictly prohibited.
- This project **does not endorse or support any malicious or illegal activities**.
- Use of this tool in violation of applicable laws or the [OpenAI Usage Policies](https://openai.com/policies/usage-policies) will result in immediate suspension of API access by OpenAI and may have legal consequences.
- By using this tool, you agree to take full responsibility for your actions and consequences thereof.
- Always comply with local laws, regulations, and organizational policies when conducting any security testing.

---

## Recommended Best Practices

- Only test systems for which you have documented permission (e.g., through a signed agreement).
- Use this tool in controlled environments or lab setups for learning and development.
- Report any vulnerabilities discovered responsibly to the appropriate parties.
- Respect privacy, data protection, and ethical guidelines at all times.
