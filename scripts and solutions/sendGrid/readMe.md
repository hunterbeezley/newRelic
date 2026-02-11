## SendGrid Suppression Removal - Multi-Account Support

This directory contains Python scripts for managing email suppressions across **7 New Relic SendGrid accounts** (1 parent + 6 sub-accounts).

---

**📘 New to this tool? Non-technical user? Start here:**
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Simple step-by-step guide for beginners (no Python/coding experience needed!)

**👨‍💻 Technical users:** Continue reading below for detailed documentation.

---

### Multi-Account Architecture

The scripts automatically check and remove suppressions across **all 7 New Relic SendGrid accounts**:
- **`parent`** - **CRITICAL**: Parent account that captures emails not in sub-accounts
- `newrelic.notifications.production`
- `newrelic.notifications.staging`
- `newrelic.notifications.eu-production`
- `issues.newrelic.com`
- `noreply_gnar`
- `authentication.newrelic`

**Why the parent account matters:**
- 🔴 **Parent account captures emails that sub-accounts do not**
- 🔴 **Must always check parent + all sub-accounts for complete coverage**
- 🔴 **Skipping parent account will miss suppressions**

**Key Benefits:**
- ✅ **Complete coverage** - Checks parent + all 6 sub-accounts automatically
- ✅ **Single operation** - One command handles all 7 accounts
- ✅ **Detailed reporting** - See which account(s) have suppressions
- ✅ **Shared API keys** - GTS team shares keys via 1Password vault

### Script: `remove_suppressions.py`

Automates the removal of email addresses from SendGrid suppression lists with three modes:
1. **Single email** - Remove a single email address
2. **Bulk CSV** - Remove emails from a CSV file
3. **Domain-based** - Find and remove all emails matching a domain (e.g., all @newrelic.com)

**Important:** SendGrid has multiple suppression lists:
- **global** - Global suppressions (manual unsubscribes)
- **bounces** - Hard bounces (email doesn't exist, mailbox full, etc.)
- **blocks** - Temporary blocks from ISPs
- **spam_reports** - Users marked email as spam
- **invalid_emails** - Failed email validation

By default, the script removes emails from **ALL 7 accounts** (parent + sub-accounts) and **ALL** suppression lists. Use `--lists` to target specific lists.

### Setup

**For non-technical users:** See [GETTING_STARTED.md](GETTING_STARTED.md) for a beginner-friendly guide.

**For technical users:**

1. **Run the setup script (recommended):**
   ```bash
   cd /Users/hbeezley/Desktop/new_relic/scripts/sendGrid
   ./setup.sh
   ```

   This automated script will:
   - Check Python 3.7+ is installed
   - Create virtual environment
   - Install dependencies
   - Configure SSL certificates from macOS Keychain (macOS only)
   - Create .env from template
   - Test connections to all accounts
   - Create logs directory

2. **Or set up manually:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.template .env
   # Edit .env with your API keys
   ```

2. **Configure API keys (GTS Team):**
   - Get API keys from **1Password GTS vault** (shared by team)
   - Update `.env` file with all 7 account keys (parent + 6 sub-accounts):
     ```bash
     # SendGrid API Keys for New Relic Accounts

     # Parent Account (CRITICAL: Captures emails not in sub-accounts)
     SENDGRID_PARENT_KEY='SG.xxx...'

     # Sub-Accounts
     SENDGRID_NEWRELIC_NOTIFICATIONS_PRODUCTION_KEY='SG.xxx...'
     SENDGRID_NEWRELIC_NOTIFICATIONS_STAGING_KEY='SG.xxx...'
     SENDGRID_NEWRELIC_NOTIFICATIONS_EU_PRODUCTION_KEY='SG.xxx...'
     SENDGRID_ISSUES_NEWRELIC_COM_KEY='SG.xxx...'
     SENDGRID_NOREPLY_GNAR_KEY='SG.xxx...'
     SENDGRID_AUTHENTICATION_NEWRELIC_KEY='SG.xxx...'
     ```

3. **Test connections:**
   ```bash
   python3 test_connection.py
   ```
   This will test all 7 accounts and confirm API keys are valid.

4. **Prepare CSV file (for bulk mode):**
   - Create a CSV with email addresses (one per line or in first column)
   - See `sample_emails.csv` for format example

### Usage

**Quick way (using run.sh wrapper):**
```bash
# Test connections
./run.sh test

# Check suppressions
./run.sh check user@example.com
# Remove suppressions
./run.sh remove --email user@example.com --dry-run```

**Traditional way (manual venv activation):**

First activate the virtual environment:
```bash
source venv/bin/activate
```

Then run scripts:

**Check which suppression lists contain an email (checks ALL 7 accounts):**
```bash
python3 check_suppressions.py user@example.com```

**Example output:**
```
Checking suppression lists for: user@example.com
================================================================================
Loaded 7 SendGrid account(s): parent, newrelic.notifications.production, ...

================================================================================
ACCOUNT: parent
================================================================================

✓ FOUND in Bounces
  Reason:  550 5.1.1 User unknown
  Created: 2025-01-15
  DELETE endpoint: DELETE /v3/suppression/bounces/user@example.com

- Not in Global Suppressions
- Not in Blocks

================================================================================
ACCOUNT: newrelic.notifications.production
================================================================================

- Not in any suppression lists

================================================================================
ACCOUNT: issues.newrelic.com
================================================================================

✓ FOUND in Global Suppressions
  Reason:  Unsubscribed
  Created: 2025-01-10

================================================================================
OVERALL SUMMARY
================================================================================
Email found in 2 account(s), 2 list(s) total:

  parent:
    - Bounces
  issues.newrelic.com:
    - Global Suppressions
```

#### Mode 1: Single Email

**Remove a single email from ALL accounts (dry run first):**
```bash
python3 remove_suppressions.py --email user@example.com --dry-run```

**Remove a single email from ALL accounts (execute):**
```bash
python3 remove_suppressions.py --email user@example.com```

**Note:** The script automatically:
1. Checks all 7 accounts (parent + 6 sub-accounts) for the email
2. Shows which account(s) have the email suppressed
3. Removes from ALL accounts where found
4. Provides detailed per-account results

#### Mode 2: Bulk CSV

**Basic usage (removes from ALL accounts and ALL lists):**
```bash
python3 remove_suppressions.py --csv emails.csv```

**Dry run (preview without making changes):**
```bash
python3 remove_suppressions.py --csv emails.csv --dry-run```

**Note:** For bulk operations, the script:
1. Checks each email across all 7 accounts (parent + 6 sub-accounts)
2. Shows per-account findings before removal
3. Removes from all accounts where found
4. Provides summary of operations per account

**Remove only from bounces:**
```bash
python3 remove_suppressions.py --csv emails.csv --lists bounces```

**Remove from bounces and blocks only:**
```bash
python3 remove_suppressions.py --csv emails.csv --lists bounces blocks```

**Remove from all except global suppressions:**
```bash
python3 remove_suppressions.py --csv emails.csv --lists bounces blocks spam_reports invalid_emails```

**Skip confirmation (automation mode):**
```bash
python3 remove_suppressions.py --csv emails.csv --no-confirm```

#### Mode 3: Domain-Based Search

**Find and remove all emails from a domain (dry run first):**
```bash
python3 remove_suppressions.py --domain @newrelic.com --dry-run```

**Find and remove all emails from a domain (execute):**
```bash
python3 remove_suppressions.py --domain @newrelic.com```

**Domain search with specific lists only:**
```bash
python3 remove_suppressions.py --domain newrelic.com --lists bounces blocks```

**Note:** Domain-based search will:
1. Fetch all suppressions from each configured list (may take a few minutes for large lists)
2. Filter emails matching the specified domain
3. **Display matching emails WITH suppression reasons** (critical for customer communication)
4. **Automatically export full details to CSV** (includes email, account, list, reason, created date, status)
5. Remove matching emails from the lists after confirmation

**Suppression details shown:**
- Which suppression list(s) the email is in (global, bounces, blocks, spam_reports, invalid_emails)
- Reason for suppression (bounce reason, spam report, etc.)
- Date created/added to suppression list
- Status (if available)

This information is **critical for explaining to customers why they were suppressed** and is displayed before removal.

#### General Options

**View all options:**
```bash
python3 remove_suppressions.py --help
```

### Diagnostic Tool: `check_suppressions.py`

Before removing suppressions, use this tool to check which lists contain the email **across all 7 accounts** (parent + 6 sub-accounts):

```bash
python3 check_suppressions.py user@example.com```

This will show:
- Which **account(s)** have the email suppressed (including parent account)
- Which **suppression lists** contain the email (per account)
- **Reason for suppression** (bounce reason, spam report date, etc.)
- **Date created** (when the email was added to the list)
- The DELETE endpoint needed for each list

**Example output:**
```
Checking suppression lists for: user@example.com
================================================================================
Loaded 7 SendGrid account(s): parent, newrelic.notifications.production, ...

================================================================================
ACCOUNT: parent
================================================================================

✓ FOUND in Bounces
  Reason:  550 5.1.1 The email account that you tried to reach does not exist
  Created: 2024-01-15 14:23:45
  DELETE endpoint: DELETE /v3/suppression/bounces/user@example.com

- Not in Global Suppressions
- Not in Blocks

================================================================================
ACCOUNT: newrelic.notifications.production
================================================================================

- Not in any suppression lists
...

================================================================================
OVERALL SUMMARY
================================================================================
Email found in 2 account(s), 3 list(s) total:

  parent:
    - Bounces
  issues.newrelic.com:
    - Global Suppressions
    - Bounces
```

This information is **critical for customer communication** - it explains exactly why their emails were suppressed and helps them understand what action to take.

### Understanding Suppression Reasons (Critical for Customer Communication)

When emails are suppressed by SendGrid, there's always a reason. Understanding these reasons is **essential for customer communication**:

**Common suppression reasons by list type:**

- **Bounces**: `550 5.1.1 User unknown`, `550 Mailbox full`, `554 Permanent failure`
  - **Customer action**: Fix the email address or increase mailbox capacity

- **Blocks**: `421 Service temporarily unavailable`, `450 Sender IP blocked`
  - **Customer action**: Usually temporary; may resolve on its own or require ISP contact

- **Spam Reports**: Date the user marked the email as spam
  - **Customer action**: User must explicitly opt back in; requires consent

- **Invalid Emails**: `Invalid email syntax`, `Domain does not exist`
  - **Customer action**: Correct the email format or domain

- **Global Suppressions**: Date of manual unsubscribe
  - **Customer action**: User must explicitly re-subscribe; requires consent

**Why this matters:**
- Helps customers understand the root cause
- Guides them on corrective actions
- Meets compliance requirements (CAN-SPAM, GDPR)
- Prevents future suppressions

**Always export and review suppression reasons before removing** to ensure customers understand why they were suppressed and have taken corrective action.

### Safety Features

1. **Dry Run Mode** - Test the script without making actual API calls
2. **Email Validation** - Validates email format before processing
3. **Rate Limiting** - Configurable delay between API calls (default: 0.1s)
4. **Confirmation Prompt** - Requires user confirmation before execution
5. **Error Logging** - Detailed logging to timestamped log files
6. **Summary Report** - Shows success/failure statistics at completion
7. **List Selection** - Target specific suppression lists or all lists
8. **Suppression Reason Display** - Shows why each email was suppressed (for customer communication)
9. **Auto CSV Export** - Domain mode automatically exports suppression details for sharing with customers

### Output

The script generates:
- **Console output** - Real-time progress with status indicators
- **Log file** - Detailed timestamped log in `logs/` directory (`logs/suppression_removal_YYYYMMDD_HHMMSS.log`)
- **Summary report** - Final statistics including failures

**Viewing logs:**
```bash
# View most recent log
ls -t logs/*.log | head -1 | xargs cat

# Tail the most recent log
ls -t logs/*.log | head -1 | xargs tail -f
```

### CSV Format

The CSV file should contain email addresses. Supported formats:

**With header:**
```csv
email
user1@example.com
user2@example.com
```

**Without header:**
```csv
user1@example.com
user2@example.com
```

The script automatically detects headers like: `email`, `emails`, `email address`, `address`

### Error Handling

The script handles various error scenarios:
- Invalid email formats (skipped with warning)
- Network timeouts (logged as failed)
- Connection errors (logged as failed)
- API errors (logged with status code and message)
- 404 responses (treated as success - email already removed)

### Exit Codes

- `0` - Success (all emails processed successfully)
- `1` - Partial failure (some emails failed to process)
- `130` - Cancelled by user (Ctrl+C)

### Troubleshooting

**SSL Certificate Errors (Corporate Networks)**

If you see `SSL: CERTIFICATE_VERIFY_FAILED` errors, run the setup script to configure SSL certificates:

```bash
./setup.sh
```

The setup script (on macOS) will:
- Extract trusted certificates from your System Keychain
- Combine them with Python's certifi bundle
- Configure the `REQUESTS_CA_BUNDLE` environment variable
- Test the SSL connection

**If not on macOS or if issues persist:**
- The `--no-verify-ssl` flag is available as a fallback (not recommended)
- Contact IT about corporate certificate configuration

**Connection Errors**

If you get generic connection errors:
- Check your internet connectivity
- Verify your API key is correct in `.env`
- Run `python3 test_connection.py` for detailed diagnostics
- Check if your firewall/proxy is blocking SendGrid API access

---

## Multi-Account Management

### Understanding the 7 SendGrid Accounts (1 Parent + 6 Sub-Accounts)

New Relic uses **7 separate SendGrid accounts** for different purposes:

**Parent Account:**
1. **parent** - 🔴 **CRITICAL**: Captures emails that sub-accounts do not handle

**Sub-Accounts:**
2. **newrelic.notifications.production** - Production notification emails
3. **newrelic.notifications.staging** - Staging environment notifications
4. **newrelic.notifications.eu-production** - EU region production notifications
5. **issues.newrelic.com** - Issue tracking and support emails
6. **noreply_gnar** - No-reply automated emails (GNAR system)
7. **authentication.newrelic** - Authentication and security emails

### Why the Parent Account is Critical

🔴 **The parent account captures emails that sub-accounts do not handle**
- Sub-accounts have specific scopes/purposes
- Emails outside those scopes fall back to the parent account
- **Skipping the parent account will miss suppressions**

### Why Check All Accounts?

An email address might be suppressed in one, some, or all accounts. To ensure emails can be delivered:
- ✅ **Always check parent + all sub-accounts** - Don't assume which account has the suppression
- ✅ **Remove from all accounts** - Even if found in just one, remove from all for consistency
- ✅ **Provide customer visibility** - Show them which accounts had suppressions
- ✅ **Parent account is mandatory** - Never skip it

### API Key Management

**For GTS Team:**
- API keys are stored in **1Password GTS shared vault**
- Each key is specific to one SendGrid account
- Keys have suppression management permissions
- **Never commit API keys to git** - they're in `.env` which is gitignored

**Updating keys:**
1. Get new keys from 1Password vault
2. Update `.env` file with new values
3. Run `python3 test_connection.py` to verify all keys work
4. Share updated `.env` with team via secure channel (not email/Slack)

### Troubleshooting Multi-Account Issues

**"Failed to load API keys from .env"**
- Check that `.env` file exists
- Verify keys start with `SG.`
- Ensure keys are not placeholder values (`your_key_here`)
- Run `python3 test_connection.py` to test each key

**"Some accounts failed authentication"**
- One or more API keys may be invalid or expired
- Check 1Password vault for updated keys
- Test individual accounts with `test_connection.py`
- Contact SendGrid admin if keys need regeneration

**"Email found in some accounts but not others"**
- This is normal - suppressions are per-account
- Script will remove from all accounts where found
- Some accounts may never have seen the email address

**Performance considerations:**
- Checking 7 accounts (parent + 6 sub-accounts) takes ~7x longer than single account
- Domain-based searches can take several minutes (fetching all suppressions from 7 accounts)
- Use `--dry-run` first for large operations
- Consider `--lists` flag to limit which lists are checked
- Parent account must always be checked - do not skip it to save time

---

## SendGrid API Reference

Using api key in /.env, the script sends a DELETE to https://api.sendgrid.com



Operation overview


DELETE/v3/asm/suppressions/global/{email}
Base url: https://api.sendgrid.com (for global users and subusers)
Base url: https://api.eu.sendgrid.com (for EU regional subusers)
This endpoint allows you to remove an email address from the global suppressions group.

Deleting a suppression group will remove the suppression, meaning email will once again be sent to the previously suppressed addresses. This should be avoided unless a recipient indicates they wish to receive email from you again. You can use our bypass filters to deliver messages to otherwise suppressed addresses when exceptions are required.

Operation details


Authentication


API Key
Headers


Property nameTypeRequiredDescription
Authorization
string
required
Default:
Bearer <<YOUR_API_KEY_HERE>>
on-behalf-of
string
Optional
The on-behalf-of header allows you to make API calls from a parent account on behalf of the parent's Subusers or customer accounts. You will use the parent account's API key when using this header. When making a call on behalf of a customer account, the property value should be "account-id" followed by the customer account's ID (e.g., on-behalf-of: account-id <account-id>). When making a call on behalf of a Subuser, the property value should be the Subuser's username (e.g., on-behalf-of: <subuser-username>). It is important to use the Base URL that corresponds to the region of the account or Subuser you specify in the on-behalf-of header. See On Behalf Of for more information.

Path parameters


Property nameTypeRequiredDescription
email
string
required
The email address of the global suppression you want to retrieve. Or, if you want to check if an email address is on the global suppressions list, enter that email address here.

Responses


204
No response body.
Delete a Global Suppression

Node.js

Report code block

Copy code block
const client = require("@sendgrid/client");
client.setApiKey(process.env.SENDGRID_API_KEY);

const email = "brian12@example.net";

const request = {
  url: `/v3/asm/suppressions/global/${email}`,
  method: "DELETE",
};

client
  .request(request)
  .then(([response, body]) => {
    console.log(response.statusCode);
    console.log(response.body);
  })
  .catch((error) => {
    console.error(error);
  });
