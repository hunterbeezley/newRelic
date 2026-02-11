#!/usr/bin/env python3
"""
SendGrid API Connection Test

Tests connectivity and API key validity before running the main script.
"""

import os
import sys
import requests
from pathlib import Path


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


def test_api_key_format(api_key):
    """Test if API key has correct format."""
    print("\n1. Testing API Key Format...")

    if not api_key:
        print("   ❌ API key is empty")
        return False

    if not api_key.startswith('SG.'):
        print(f"   ❌ API key should start with 'SG.' but starts with: {api_key[:10]}...")
        return False

    print(f"   ✓ API key format looks correct: {api_key[:10]}...{api_key[-10:]}")
    return True


def test_network_connectivity():
    """Test basic network connectivity."""
    print("\n2. Testing Network Connectivity...")

    try:
        response = requests.get('https://api.sendgrid.com', timeout=5)
        print(f"   ✓ Can reach SendGrid API (status: {response.status_code})")
        return True
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Connection Timeout")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_api_authentication(api_key):
    """Test API authentication with a simple GET request."""
    print("\n3. Testing API Authentication...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Test with a simple GET request to the API
    # Using the suppression groups endpoint as a test
    url = "https://api.sendgrid.com/v3/asm/groups"

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"   ✓ API key is valid and authenticated successfully")
            return True
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed (401 Unauthorized)")
            print(f"   Response: {response.text}")
            return False
        elif response.status_code == 403:
            print(f"   ❌ API key lacks permissions (403 Forbidden)")
            print(f"   Response: {response.text}")
            return False
        else:
            print(f"   ⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        print("\n   Try setting verify=False in requests (insecure but may help diagnose)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        print("\n   Possible causes:")
        print("   - Firewall blocking connections")
        print("   - Proxy configuration needed")
        print("   - Network connectivity issues")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Request Timeout")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
        return False


def test_delete_endpoint(api_key):
    """Test DELETE endpoint with a test email."""
    print("\n4. Testing DELETE Endpoint (dry test)...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Use a clearly test email that won't exist
    test_email = "nonexistent_test@example.com"
    url = f"https://api.sendgrid.com/v3/asm/suppressions/global/{test_email}"

    try:
        response = requests.delete(url, headers=headers, timeout=10)

        if response.status_code == 204:
            print(f"   ✓ DELETE successful (email was in suppressions)")
            return True
        elif response.status_code == 404:
            print(f"   ✓ DELETE endpoint working (404 = email not in suppressions - expected)")
            return True
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed")
            return False
        elif response.status_code == 403:
            print(f"   ❌ Permission denied - API key may not have suppression management rights")
            return False
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("SendGrid API Connection Test - Multi-Account (Parent + 6 Sub-Accounts)")
    print("="*80)

    # Load API keys
    print("\nLoading API keys from .env...")
    api_keys = load_api_keys()

    if not api_keys:
        print("\n❌ Failed to load API keys from .env")
        print("\nMake sure .env contains valid SendGrid API keys:")
        print("  SENDGRID_<ACCOUNT_NAME>_KEY='SG.xxx...'")
        print("\nExample:")
        print("  SENDGRID_NEWRELIC_NOTIFICATIONS_PRODUCTION_KEY='SG.xxx...'")
        return 1

    print(f"✓ Loaded {len(api_keys)} account(s): {', '.join(api_keys.keys())}\n")

    # Test network connectivity once (shared across all accounts)
    print("="*80)
    print("SHARED TESTS")
    print("="*80)
    network_ok = test_network_connectivity()

    # Test each account
    all_results = {}

    for account_name, api_key in api_keys.items():
        print(f"\n{'='*80}")
        print(f"TESTING ACCOUNT: {account_name}")
        print(f"{'='*80}")
        print(f"API Key: {api_key[:10]}...{api_key[-10:]}")

        # Run tests for this account
        results = []
        results.append(("API Key Format", test_api_key_format(api_key)))
        results.append(("API Authentication", test_api_authentication(api_key)))
        results.append(("DELETE Endpoint", test_delete_endpoint(api_key)))

        all_results[account_name] = results

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80)

    print(f"\n{'Network Connectivity':<30} {'✓ PASS' if network_ok else '✗ FAIL'}")

    for account_name, results in all_results.items():
        print(f"\n{account_name}:")
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {test_name:<28} {status}")

    # Check if all tests passed
    all_passed = network_ok and all(
        all(result for _, result in results)
        for results in all_results.values()
    )

    print("\n" + "="*80)
    if all_passed:
        print("✅ All tests passed for all accounts! The scripts should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Fix the issues above before running the main scripts.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
