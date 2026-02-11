# Getting Started - SendGrid Suppression Management Tool

**For non-technical users** - No Python or coding experience required!

---

## What This Tool Does

This tool helps you remove email addresses from SendGrid suppression lists across all 7 New Relic SendGrid accounts. When emails get "suppressed," they can't receive emails from New Relic. This tool fixes that problem.

**The tool checks 7 accounts automatically:**
- Parent account (critical!)
- 6 sub-accounts (production, staging, EU, issues, GNAR, authentication)

---

## Prerequisites

Before you start, you need:

1. **Python 3.7 or higher** installed on your computer
   - Check if you have it: Open Terminal and type `python3 --version`
   - If not installed: Download from [python.org](https://www.python.org/downloads/)

2. **SendGrid API keys** from 1Password GTS vault
   - You need all 7 API keys (ask your team lead if you don't have access)
   - Each key starts with `SG.` followed by a long string

3. **Terminal/Command Line** access
   - macOS: Use "Terminal" app (in Applications > Utilities)
   - Linux: Use your terminal emulator
   - Windows: Use Command Prompt or PowerShell

---

## Step-by-Step Setup (First Time Only)

### Step 1: Open Terminal

1. Open Terminal (macOS) or Command Prompt (Windows)
2. Navigate to the SendGrid tool directory:
   ```bash
   cd /Users/hbeezley/Desktop/new_relic/scripts/sendGrid
   ```
   _(Replace the path above with wherever you downloaded the files)_

### Step 2: Run the Setup Script

Simply run:
```bash
./setup.sh
```

**What the script does automatically:**
- ✅ Checks that Python 3 is installed
- ✅ Creates a virtual environment (keeps dependencies isolated)
- ✅ Installs required packages
- ✅ Configures SSL certificates from macOS Keychain (macOS only)
- ✅ Creates your `.env` configuration file
- ✅ Tests connections to SendGrid

### Step 3: Configure API Keys

When prompted, you have **two options**:

**Option 1 (Recommended): Edit manually**
1. Get all 7 API keys from 1Password GTS vault
2. Open the `.env` file in a text editor:
   ```bash
   nano .env
   ```
3. Replace each `SG.your_key_here` with the actual API key
4. Save the file (Ctrl+O, then Enter, then Ctrl+X)
5. Run setup again to test: `./setup.sh`

**Option 2: Interactive (guided)**
1. Choose option 2 when prompted
2. Paste each API key when asked
3. The script validates and saves them for you

### Step 4: Test Connections

The setup script automatically tests all 7 accounts. You should see:
```
✓ All connection tests passed!
```

If you see errors, check that your API keys are correct.

---

## Daily Usage

You have **two ways** to use the tool:

### Option 1: Use the Convenience Wrapper (Easiest!)

The `run.sh` script automatically handles the virtual environment for you:

```bash
cd /Users/hbeezley/Desktop/new_relic/scripts/sendGrid
./run.sh <command> [arguments]
```

**Available commands:**
- `test` - Test connections
- `check <email>` - Check suppressions
- `remove <options>` - Remove suppressions

**Examples:**
```bash
# Test connections
./run.sh test

# Check an email
./run.sh check user@example.com

# Remove single email (dry run)
./run.sh remove --email user@example.com --dry-run

# Remove from CSV
./run.sh remove --csv emails.csv
```

### Option 2: Manual Activation (Advanced)

If you prefer to activate the environment yourself:

```bash
cd /Users/hbeezley/Desktop/new_relic/scripts/sendGrid
source venv/bin/activate
```

You'll see `(venv)` appear in your terminal prompt. Now you can run any of the scripts below.

---

## Common Tasks

### Check if an Email is Suppressed

Before removing anything, check which accounts/lists have the email:

**Using run.sh (easiest):**
```bash
./run.sh check user@example.com```

**Or manually:**
```bash
python3 check_suppressions.py user@example.com```

**Output shows:**
- Which account(s) have the email suppressed
- Which suppression lists (bounces, blocks, spam, etc.)
- Why the email was suppressed (bounce reason, spam report date)
- When it was added to the list

### Remove a Single Email (Recommended: Dry Run First)

**Using run.sh (easiest):**

**Step 1: Dry run** (preview what would happen):
```bash
./run.sh remove --email user@example.com --dry-run```

**Step 2: Execute** (actually remove):
```bash
./run.sh remove --email user@example.com```

**Or manually:**
```bash
python3 remove_suppressions.py --email user@example.com --dry-runpython3 remove_suppressions.py --email user@example.com```

### Remove Multiple Emails from a CSV File

**Step 1: Prepare your CSV file**

Create a file called `emails.csv` with one email per line:
```csv
email
user1@example.com
user2@example.com
user3@example.com
```

**Step 2: Run with run.sh (easiest):**

**Dry run first:**
```bash
./run.sh remove --csv emails.csv --dry-run```

**Execute:**
```bash
./run.sh remove --csv emails.csv```

**Or manually:**
```bash
python3 remove_suppressions.py --csv emails.csv --dry-runpython3 remove_suppressions.py --csv emails.csv```

### Remove All Emails from a Domain

Find and remove all `@newrelic.com` emails:

**Using run.sh (easiest):**
```bash
# Dry run first
./run.sh remove --domain @newrelic.com --dry-run
# Execute
./run.sh remove --domain @newrelic.com```

**Or manually:**
```bash
python3 remove_suppressions.py --domain @newrelic.com --dry-runpython3 remove_suppressions.py --domain @newrelic.com```

This will:
- Search all 7 accounts for matching emails
- Show you all found emails with suppression reasons
- Export full details to CSV
- Remove after you confirm

---

## Important Notes

### Always Use `--dry-run` First

Before executing any removal, do a dry run:

```bash
python3 remove_suppressions.py --email user@example.com --dry-run```

This shows you what would happen without actually making changes.

### Understanding Suppression Types

- **Bounces** - Email doesn't exist, mailbox full, permanent failure
- **Blocks** - Temporary ISP blocks, usually resolves on its own
- **Spam Reports** - User marked email as spam (requires user consent to remove)
- **Global Suppressions** - Manual unsubscribes (requires user consent to remove)
- **Invalid Emails** - Failed email validation (syntax errors, bad domains)

### Logs are Saved Automatically

All operations are logged to the `logs/` directory with timestamps:
```bash
# View most recent log
ls -t logs/*.log | head -1 | xargs cat
```

---

## Troubleshooting

### "SSL: CERTIFICATE_VERIFY_FAILED"

**Solution:** Run the setup script to configure SSL certificates (macOS only)

```bash
./setup.sh
```

The setup script will automatically extract certificates from your macOS Keychain and configure Python to use them.

**If not on macOS or if SSL issues persist:**
- You can use the `--no-verify-ssl` flag as a fallback (not recommended for production)
- Contact your IT team about corporate certificate configuration

### "Failed to load API keys from .env"

**Solution:** Check that your `.env` file exists and has valid keys

```bash
# Check file exists
ls -la .env

# Test connections
python3 test_connection.py
```

### "Some connection tests failed"

**Possible causes:**
- Invalid API key - verify in 1Password
- Expired API key - get new key from SendGrid admin
- Network/firewall issues - check internet connection

**Solution:** Fix the API keys in `.env` and test again:
```bash
nano .env
# Fix the keys
python3 test_connection.py
```

### "command not found: python3"

**Solution:** Install Python 3 from [python.org](https://www.python.org/downloads/)

### Script errors or unexpected behavior

**Solution:** View the full error in the logs:
```bash
ls -t logs/*.log | head -1 | xargs cat
```

---

## Getting Help

### View Full Documentation

```bash
cat readMe.md
```

### View Script Help

```bash
python3 remove_suppressions.py --help
```

### Test Connections

```bash
python3 test_connection.py
```

### Ask Your Team

If you're stuck, ask in your team's Slack channel or contact your team lead.

---

## Quick Reference Card

### Using run.sh (Recommended - Easiest!)

Copy and paste these commands as needed:

```bash
# Navigate to directory
cd /Users/hbeezley/Desktop/new_relic/scripts/sendGrid

# Test connections
./run.sh test

# Check an email
./run.sh check user@example.com
# Remove single email (dry run)
./run.sh remove --email user@example.com --dry-run
# Remove single email (execute)
./run.sh remove --email user@example.com
# Remove from CSV (dry run)
./run.sh remove --csv emails.csv --dry-run
# Remove from CSV (execute)
./run.sh remove --csv emails.csv
# View recent log
ls -t logs/*.log | head -1 | xargs cat
```

### Manual Method (Advanced)

If you prefer to manage the virtual environment yourself:

```bash
# Navigate to directory
cd /Users/hbeezley/Desktop/new_relic/scripts/sendGrid

# Activate environment (do this first every time)
source venv/bin/activate

# Check an email
python3 check_suppressions.py user@example.com
# Remove single email (dry run)
python3 remove_suppressions.py --email user@example.com --dry-run
# Remove single email (execute)
python3 remove_suppressions.py --email user@example.com
# Remove from CSV (dry run)
python3 remove_suppressions.py --csv emails.csv --dry-run
# Remove from CSV (execute)
python3 remove_suppressions.py --csv emails.csv
# Test connections
python3 test_connection.py

# View recent log
ls -t logs/*.log | head -1 | xargs cat

# Deactivate environment (when done)
deactivate
```

---

## Summary Checklist

Before you start using the tool, make sure:

- [ ] Python 3.7+ is installed (`python3 --version`)
- [ ] You've run `./setup.sh` successfully
- [ ] SSL certificates configured (automatic on macOS)
- [ ] You have all 7 API keys configured in `.env`
- [ ] Connection tests pass (`python3 test_connection.py`)
- [ ] You know how to activate the virtual environment (`source venv/bin/activate`)
- [ ] You understand to use `--dry-run` first

**You're ready to go!**
