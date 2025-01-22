import requests
import json
import argparse
import urllib.parse
import time

BASE_URL = 'https://URL'
TOKEN = 'YOUR_TOKEN_HERE'

headers = {
    'accept': 'application/json',
    'authorization': f'Bearer {TOKEN}',
    'content-type': 'application/json',
    'cookie': f'token={TOKEN}'
}

def parse_args():
    parser = argparse.ArgumentParser(description='Update model ACLs')
    parser.add_argument('--show-disabled', action='store_true',
                      help='Show disabled models in the list')
    parser.add_argument('--token', type=str, help='API token')
    parser.add_argument('--replace', action='store_true',
                      help='Replace existing group access instead of appending')
    parser.add_argument('--debug', action='store_true',
                      help='Show debug information including API requests and responses')
    parser.add_argument('--proxy', type=str,
                      help='Proxy URL (e.g., http://127.0.0.1:8080)')
    return parser.parse_args()

def parse_range_string(range_str, max_value):
    """Parse a range string like '1-5,7,9-11' into a list of numbers"""
    numbers = set()
    if range_str.lower() == 'all':
        return list(range(1, max_value + 1))
    
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = map(str.strip, part.split('-'))
            try:
                start, end = int(start), int(end)
                if start > end:
                    start, end = end, start
                if start < 1 or end > max_value:
                    raise ValueError(f"Range {start}-{end} is out of bounds (1-{max_value})")
                numbers.update(range(start, end + 1))
            except ValueError as e:
                if "is out of bounds" in str(e):
                    raise
                print(f"Invalid range: {part}")
                continue
        else:
            try:
                num = int(part)
                if num < 1 or num > max_value:
                    raise ValueError(f"Number {num} is out of bounds (1-{max_value})")
                numbers.add(num)
            except ValueError as e:
                if "is out of bounds" in str(e):
                    raise
                print(f"Invalid number: {part}")
                continue
    
    return sorted(list(numbers))

def get_groups():
    response = requests.get(f'{BASE_URL}/api/v1/groups/', headers=headers, proxies=proxies)
    return response.json()

def get_models(show_disabled=False):
    """Get models list with their status and info"""
    response = requests.get(f'{BASE_URL}/api/models', headers=headers, proxies=proxies)
    all_models = response.json()['data']
    
    filtered_models = []
    for model in all_models:
        model_info = model.get('info', {})
        is_active = model_info.get('is_active', True)
        if show_disabled or is_active:

            default_access_control = {
                'read': {'group_ids': [], 'user_ids': []},
                'write': {'group_ids': [], 'user_ids': []}
            }
            
            access_control = (model.get('access_control') or 
                            model_info.get('access_control') or 
                            default_access_control)
            
            processed_model = {
                'id': model['id'],
                'name': model['name'],
                'object': model['object'],
                'created': model['created'],
                'owned_by': model['owned_by'],
                'is_active': is_active,
                'access_control': access_control
            }
            if 'pipe' in model:
                processed_model['pipe'] = model['pipe']
            
            filtered_models.append(processed_model)
    
    return filtered_models

def update_model_acl(model, new_group_ids, replace=False, debug=False):
    model_data = {
        'id': model['id'],
        'base_model_id': None,
        'name': model['name'],
        'meta': {
            'profile_image_url': '/static/favicon.png',
            'description': '',
            'suggestion_prompts': None,
            'tags': [],
            'capabilities': {
                'vision': True,
                'citations': True
            },
            'toolIds': ['web_search']
        },
        'params': {},
        'object': model['object'],
        'created': model['created'],
        'owned_by': model['owned_by'],
        'is_active': True
    }
    
    if 'pipe' in model:
        model_data['pipe'] = model['pipe']
    
    if replace:
        read_group_ids = new_group_ids
    else:
        current_group_ids = (model.get('access_control', {})
                           .get('read', {})
                           .get('group_ids', []))
        read_group_ids = list(set(current_group_ids + new_group_ids))
    
    model_data['access_control'] = {
        'read': {'group_ids': read_group_ids, 'user_ids': []},
        'write': {'group_ids': [], 'user_ids': []}
    }
    
    # Добавляем текущее время для updated_at и created_at
    current_timestamp = int(time.time())
    model_data.update({
        'updated_at': current_timestamp,
        'created_at': current_timestamp
    })
    
    if debug:
        print(f"\nSending update request for {model_data['name']}:")
        print(f"Request URL: {BASE_URL}/api/v1/models/model/update?id={urllib.parse.quote(model['id'])}")
        print("Request payload:")
        print(json.dumps(model_data, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/models/model/update?id={urllib.parse.quote(model['id'])}",
        headers=headers,
        json=model_data,
        proxies=proxies
    )
    
    if debug:
        print(f"Response status: {response.status_code}")
        print("Response body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    
    success = response.status_code == 200
    return success, read_group_ids, "Success" if success else "Failed"

def main():
    args = parse_args()
    
    # Configure global variables
    if args.token:
        global TOKEN, headers
        TOKEN = args.token
        headers['authorization'] = f'Bearer {TOKEN}'
        headers['cookie'] = f'token={TOKEN}'
    
    # Configure proxies
    global proxies
    if args.proxy:
        proxies = {
            'http': args.proxy,
            'https': args.proxy
        }
    else:
        proxies = None # Default no proxy

    try:
        print("Fetching groups..." if args.debug else "", end="")
        groups = get_groups()
        print("Fetching models..." if args.debug else "", end="")
        models = get_models(args.show_disabled)
        
        if not models:
            print("No models found!")
            return
            
        active_count = sum(1 for model in models if model.get('is_active', True))
        disabled_count = len(models) - active_count
        
        print(f"\nFound {active_count} active models" + 
              (f" ({disabled_count} disabled {'shown' if args.show_disabled else 'hidden'})" 
               if disabled_count > 0 else ""))
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return
    
    # Create groups lookup dictionary
    groups_lookup = {group['id']: group['name'] for group in groups}
    
    # Display groups
    print("\nAvailable groups:")
    for i, group in enumerate(groups, 1):
        print(f"{i}. {group['name']} ({group['description']})")
    
    # Get group selection
    while True:
        group_input = input("\nEnter group numbers (e.g., '1-3,5,7-9') or 'all' or press Enter for none: ").strip()
        if not group_input:
            selected_group_ids = []
            break
        
        try:
            group_numbers = parse_range_string(group_input, len(groups))
            selected_group_ids = [groups[i-1]['id'] for i in group_numbers]
            break
        except ValueError as e:
            print(f"Error: {e}")
            continue
    
    # Display models
    print("\nAvailable models:")
    for i, model in enumerate(models, 1):
        status = "" if model.get('is_active', True) else " [DISABLED]"
        access_control = model.get('access_control', {})
        current_groups = [groups_lookup.get(gid, gid)
                         for gid in access_control.get('read', {}).get('group_ids', [])]
        groups_info = f" (Current groups: {', '.join(current_groups)})" if current_groups else ""
        print(f"{i}. [{model['id']}] {model['name']}{status}{groups_info}")
    
    # Get model selection
    while True:
        model_input = input("\nEnter model numbers (e.g., '1-3,5,7-9') or 'all': ").strip()
        if not model_input:
            print("No models selected")
            return
        
        try:
            model_numbers = parse_range_string(model_input, len(models))
            # Save tuples (model_num, model)
            selected_models = [(i, models[i-1]) for i in model_numbers]
            break
        except ValueError as e:
            print(f"Error: {e}")
            continue

    # Show summary before proceeding
    print("\nSummary:")
    print("Selected groups:")
    for group_id in selected_group_ids:
        print(f"- {groups_lookup[group_id]}")
    
    print("\nSelected models:")
    for i, model in selected_models:
        status = "" if model.get('is_active', True) else " [DISABLED]"
        current_groups = [groups_lookup.get(gid, gid)
                         for gid in model.get('access_control', {}).get('read', {}).get('group_ids', [])]
        groups_info = f" (Current groups: {', '.join(current_groups)})" if current_groups else ""
        print(f"- [{i}] [{model['id']}] {model['name']}{status}{groups_info}")

    print(f"\nMode: {'Replace' if args.replace else 'Append'} groups")
    
    # Confirmation
    confirm = input("\nProceed with these changes? (y/N): ").lower()
    if confirm != 'y':
        print("Operation cancelled")
        return
    
    # Update models
    print("\nUpdating models...")
    total_models = len(selected_models)
    for idx, (original_num, model) in enumerate(selected_models, 1):
        try:
            success, final_group_ids, status_message = update_model_acl(
                model, 
                selected_group_ids, 
                args.replace,
                args.debug
            )
            final_groups = [groups_lookup.get(gid, gid) for gid in final_group_ids]
            print(f"[{idx}/{total_models}][#{original_num}] Updating [{model['id']}] {model['name']}: {status_message}")
            if status_message in ["Success", "Already exists"]:
                print(f"  Final groups: {', '.join(final_groups)}")
        except requests.exceptions.RequestException as e:
            print(f"[{idx}/{total_models}][#{original_num}] Error updating [{model['id']}] {model['name']}: {e}")

if __name__ == "__main__":
    main()
