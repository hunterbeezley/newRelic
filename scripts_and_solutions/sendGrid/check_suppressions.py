#!/usr/bin/env python3
"""
SendGrid Suppression Checker

Checks which suppression list(s) an email address appears in.
SendGrid has multiple suppression lists:
- Global Suppressions (unsubscribes)
- Bounces
- Blocks
- Spam Reports
- Invalid Emails

This helps determine which endpoint to use for removal.
"""

import sys
import requests
from pathlib import Path
import urllib3


def load_api_keys():
    """
    Load all SendGrid API keys from .env file.

    Returns:
        Dict mapping account name to API key, or None if no keys found
    """
    env_path = Path(__file__).parent / '.env'

    if not env_path.exists():
        print("❌ .env file not found")
        return None

    api_keys = {}

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Look for SENDGRID_*_KEY variables
            if line.startswith('SENDGRID_') and '_KEY=' in line:
                key_name, api_key = line.split('=', 1)
                api_key = api_key.strip().strip("'\"")

                # Extract friendly account name from variable name
                # SENDGRID_PARENT_KEY -> parent
                # SENDGRID_NEWRELIC_NOTIFICATIONS_PRODUCTION_KEY -> newrelic.notifications.production
                account_parts = key_name.replace('SENDGRID_', '').replace('_KEY', '').lower().split('_')

                # Convert underscores to dots for display
                if account_parts == ['parent']:
                    account_name = 'parent'
                elif 'newrelic' in account_parts and 'notifications' in account_parts:
                    # newrelic.notifications.production or newrelic.notifications.staging or newrelic.notifications.eu-production
                    idx = account_parts.index('notifications')
                    remaining = account_parts[idx+1:]
                    if 'eu' in remaining:
                        account_name = 'newrelic.notifications.eu-production'
                    else:
                        account_name = 'newrelic.notifications.' + '.'.join(remaining)
                elif 'issues' in account_parts:
                    account_name = 'issues.newrelic.com'
                elif 'noreply' in account_parts and 'gnar' in account_parts:
                    account_name = 'noreply_gnar'
                elif 'authentication' in account_parts:
                    account_name = 'authentication.newrelic'
                else:
                    account_name = '.'.join(account_parts)

                # Only add if key looks valid
                if api_key and api_key.startswith('SG.') and not api_key.endswith('your_key_here'):
                    api_keys[account_name] = api_key

    if not api_keys:
        return None

    return api_keys


def check_suppression_list(api_key, email, list_type, endpoint, verify_ssl=True):
    """
    Check if an email is in a specific suppression list.

    Args:
        api_key: SendGrid API key
        email: Email to check
        list_type: Name of the list (for display)
        endpoint: API endpoint path
        verify_ssl: Whether to verify SSL

    Returns:
        Tuple of (found: bool, details: dict or None)
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = f"https://api.sendgrid.com{endpoint}/{email}"

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=verify_ssl)

        if response.status_code == 200:
            # Possible email found - need to verify response has actual data
            try:
                data = response.json()

                # Check if data is meaningful (not empty list/dict)
                if isinstance(data, list):
                    if not data:
                        # Empty list means NOT in suppression list
                        return False, None
                    # Use first item from list
                    data = data[0]

                # Check if we have meaningful data
                if not data or (isinstance(data, dict) and not any(data.values())):
                    # Empty dict or no data means NOT in suppression list
                    return False, None

                return True, data
            except:
                return True, {"status": "found but no details"}
        elif response.status_code == 404:
            # Email not in this list
            return False, None
        else:
            return False, {"error": f"Status {response.status_code}: {response.text}"}

    except Exception as e:
        return False, {"error": str(e)}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 check_suppressions.py <email> [--no-verify-ssl]")
        print("\nExample:")
        print("  python3 check_suppressions.py user@example.com")
        print("  python3 check_suppressions.py user@example.com --no-verify-ssl")
        return 1

    email = sys.argv[1]
    verify_ssl = "--no-verify-ssl" not in sys.argv

    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("⚠️  SSL verification disabled\n")

    print(f"Checking suppression lists for: {email}")
    print("="*80)

    # Load API keys for all accounts
    api_keys = load_api_keys()
    if not api_keys:
        print("❌ Failed to load API keys from .env")
        print("\nMake sure .env contains valid SendGrid API keys:")
        print("  SENDGRID_<ACCOUNT_NAME>_KEY='SG.xxx...'")
        return 1

    print(f"Loaded {len(api_keys)} SendGrid account(s): {', '.join(api_keys.keys())}\n")

    # Define suppression lists to check
    suppression_lists = [
        ("Global Suppressions", "/v3/asm/suppressions/global", "/v3/asm/suppressions/global"),
        ("Bounces", "/v3/suppression/bounces", "/v3/suppression/bounces"),
        ("Blocks", "/v3/suppression/blocks", "/v3/suppression/blocks"),
        ("Spam Reports", "/v3/suppression/spam_reports", "/v3/suppression/spam_reports"),
        ("Invalid Emails", "/v3/suppression/invalid_emails", "/v3/suppression/invalid_emails"),
    ]

    all_found = []  # Track all findings across accounts
    account_summary = {}  # Track findings per account

    # Check each account
    for account_name, api_key in api_keys.items():
        print(f"\n{'='*80}")
        print(f"ACCOUNT: {account_name}")
        print(f"{'='*80}")

        found_in_account = []

        for list_name, endpoint, delete_endpoint in suppression_lists:
            found, details = check_suppression_list(api_key, email, list_name, endpoint, verify_ssl)

            if found:
                print(f"\n✓ FOUND in {list_name}")
                if details and "error" not in details:
                    # Pretty-print important fields for customer communication
                    reason = details.get('reason', 'N/A')
                    created = details.get('created', details.get('created_at', 'N/A'))
                    status = details.get('status', 'N/A')

                    print(f"  Reason:  {reason}")
                    print(f"  Created: {created}")
                    if status != 'N/A':
                        print(f"  Status:  {status}")

                    # Show full details if there's more info
                    if len(details) > 3:
                        print(f"  Full details: {details}")
                else:
                    print(f"  Status: Present in list")
                print(f"  DELETE endpoint: DELETE {delete_endpoint}/{email}")
                found_in_account.append(list_name)
                all_found.append((account_name, list_name, details))
            else:
                if details and "error" in details:
                    print(f"\n✗ Error checking {list_name}: {details['error']}")
                else:
                    print(f"\n- Not in {list_name}")

        if found_in_account:
            account_summary[account_name] = found_in_account
        else:
            print(f"\n✓ Not found in any lists in this account")

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)

    if all_found:
        print(f"Email found in {len(account_summary)} account(s), {len(all_found)} list(s) total:\n")
        for account_name, lists in account_summary.items():
            print(f"  {account_name}:")
            for list_name in lists:
                print(f"    - {list_name}")
    else:
        print("✓ Email not found in any suppression lists across all accounts")

    return 0


if __name__ == "__main__":
    sys.exit(main())
