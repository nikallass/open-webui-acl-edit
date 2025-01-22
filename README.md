# OpenWebUI Model ACL Manager
A command-line tool for managing access control lists (ACLs) for models in OpenWebUI.

## Features
- List all available models and groups
- Show/hide disabled models
- Append or replace group access rights
- Support for single models or ranges (e.g., 1-5,8,10-15)
- Proxy support
- Debug mode for troubleshooting

## Installation
1. Clone this repository
2. Install required dependencies:
```bash
pip install requests
```

## Usage
Basic usage:
```bash
python openwebui_acl.py --url https://your-openwebui-instance.com --token YOUR_TOKEN
```

### Command Line Arguments
```bash
  --url URL           Base URL of the API (e.g., https://your-openwebui-instance.com)
  --token TOKEN       API token
  --show-disabled    Show disabled models in the list
  --replace          Replace existing group access instead of appending
  --debug            Show debug information including API requests and responses
  --proxy PROXY      Proxy URL (e.g., http://127.0.0.1:8080)
```

### Examples
1. Basic usage (append mode):
```bash
python openwebui_acl.py --url https://your-openwebui-instance.com --token YOUR_TOKEN
```

2. Replace existing groups instead of appending:
```bash
python openwebui_acl.py --url https://your-openwebui-instance.com --token YOUR_TOKEN --replace
```

3. Show disabled models:
```bash
python openwebui_acl.py --url https://your-openwebui-instance.com --token YOUR_TOKEN --show-disabled
```

4. Use with proxy:
```bash
python openwebui_acl.py --url https://your-openwebui-instance.com --token YOUR_TOKEN --proxy http://127.0.0.1:8080
```

5. Debug mode:
```bash
python openwebui_acl.py --url https://your-openwebui-instance.com --token YOUR_TOKEN --debug
```

## Interactive Usage
1. The script will display available groups with their descriptions
2. Enter group numbers to select (supports ranges like "1-3,5,7-9" or "all")
3. View available models with their current group access
4. Select models to update (supports ranges like "1-3,5,7-9" or "all")
5. Review summary of changes
6. Confirm to proceed

### Example Output
```
Available groups:
1. Tech Guys
2. Marketing Guys
3. Support Guys

Enter group numbers (e.g., '1-3,5,7-9') or 'all' or press Enter for none: 1-2

Available models:
154. [openrouter_api.meta-llama/llama-3-70b-instruct] "openrouter/Meta: Llama 3 70B Instruct" (Current groups: Tech Guys)

Selected models:
- [154] [openrouter_api.meta-llama/llama-3-70b-instruct] "openrouter/Meta: Llama 3 70B Instruct" (Current groups: Support Guys)

Mode: Append groups

[1/1][#154] Updating [openrouter_api.meta-llama/llama-3-70b-instruct] "openrouter/Meta: Llama 3 70B Instruct": Success
  Final groups: Marketing Guys, Tech Guys, Support Guys
```
