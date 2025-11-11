# New Relic User Mass Deletion Tool - prod & staging

## ⚠️ CRITICAL WARNINGS ⚠️

**READ THIS ENTIRE SECTION BEFORE PROCEEDING**

- **THIS PERMANENTLY DELETES USER RECORDS** - There is no easy way to undo, recover, or rollback
- **ONLY USE FOR EXTREME EDGE-CASES** -- where hundreds of duplicate user records exist for the same email
- **ALWAYS TEST AGAINST TEST USERS FIRST** - Make sure you understand how this works against users that are safe to delete before trouching the real users (especially in prod)
- **TRACK YOUR WORK** -- ensure there is a ticket, jira, etc.
- **A USER KEY WITH PERMISSIONS TO DELETE ANY USER WILL BE REQUIRED** -- If you do not have these permissions, this script is not for you :)
- **BACKUP FIRST** - While a rollback is not possible, having an export of user Id's prior to deletion is a good idea for auditing.

**If you're unsure whether you need this tool, you probably don't. Manual deletion is safer for small batches.**

---

## What This Tool Does

This is a two-script workflow for bulk deletion of New Relic user records:

1. **filterOldUsers.py** - Filters a JSON of user metadata by creation date (e.g., "older than 30 days")
2. **massDeleteUsers.py** - Takes the filtered user IDs and deletes them via NerdGraph API

There are two folders for each version of these workflows: `userDeleteOneMonth-prod` & `userDeleteOneMonth-staging`. Follow one or both depending on needs.

**Use Case for this two-script workflow**: When accidental user provisioning creates hundreds of duplicate user records for the same email address, making manual deletion impractical.

---

## Complete Workflow

### Pre-reqs

- Python 3.6+
- New Relic User API key (for both prod & staging); associated user must have permissions to delete any NR user
- JSON export of user metadata (with at least: `id`, `created_at` fields); can be retrieved via `/user-search.service.newrelic.com/users.json?email=EMAIL_HERE`

### Initial Setup

**Use a virtual environment:**

```bash
# Navigate to the massDeleteUsers directory you'll be using:
cd userDeleteOneMonth-staging/massDeleteUsers  # or userDeleteOneMonth-prod

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate 

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list  # Should show 'requests' package
```

**Note**: You'll need to activate the virtual environment (`source venv/bin/activate`) each time you open a new terminal session before running the scripts.

### Step 1: Filter Users by Date

**Purpose**: Narrow down hundreds/thousands of user records to only those older than X days

**Location**: 
- Staging: `userDeleteOneMonth-staging/filterIds/filterOldUsers.py`
- Production: `userDeleteOneMonth-prod/filterIds/filterOldUsers.py`

**Input**: JSON file with user metadata (see example: `users.json.json`)

**Output**: Filtered JSON with just user IDs in format: `{"userIds": ["id1", "id2", ...]}`

**Run**:
```bash
cd userDeleteOneMonth-staging/filterIds  # or -prod
python filterOldUsers.py
```

**Interactive prompts**:
1. Path to your user metadata JSON file
2. Days threshold (default: 30)
3. Output file path (default: `{input_filename}_filtered.json`)

**What it does**:
- Loads your user metadata JSON
- Filters to users with `created_at` older than X days ago
- Shows you statistics (total users, filtered users, exclusions)
- Saves filtered user IDs to a new JSON file
- Handles duplicates automatically (skips them)

**Example output**:
```
======================================================================
FILTERING STATISTICS
======================================================================
Cutoff date (must be older than): 2024-10-11 12:00:00 UTC
Days threshold: 30 days ago

Total users in input file:       12
Users with valid ID:              11
Users with created date:          11

✓ Users older than threshold:     9
✗ Users too recent (< 30 days):   2
✗ Users missing ID:               1
✗ Users missing created date:     0
✗ Invalid dates:                  0
✗ Duplicate IDs (skipped):        0
======================================================================
```

### Step 2: Review Filtered Users

**CRITICAL STEP - DO NOT SKIP**

1. Open the filtered JSON file
2. Manually verify the user IDs look correct
3. Cross-reference a few IDs in New Relic UI
4. Check that the count matches your expectations
5. If anything looks wrong, STOP and investigate

**Red flags**:
- More users than expected
- User IDs you don't recognize
- Mix of different email addresses (if you're targeting one email)

### Step 3: Delete Users (Point of No Return)

**Purpose**: Execute deletion of filtered user IDs via NerdGraph API

**Location**:
- Staging: `userDeleteOneMonth-staging/massDeleteUsers/massDeleteUsers.py`
- Production: `userDeleteOneMonth-prod/massDeleteUsers/massDeleteUsers.py`

**Input**: The filtered JSON from Step 1 (format: `{"userIds": [...]}`)

**Activate virtual environment** (if not already activated):
```bash
cd userDeleteOneMonth-staging/massDeleteUsers  # or -prod
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows
```

**Setup API Key** (first time only):

**Option A - Config file (recommended)**:
```bash
cd userDeleteOneMonth-staging/massDeleteUsers  # or -prod
mkdir -p config
echo "YOUR_API_KEY_HERE" > config/api_key.txt
```

**Option B - Environment variable**:
```bash
export NEWRELIC_API_KEY="YOUR_API_KEY_HERE"
```

**Run**:
```bash
cd userDeleteOneMonth-staging/massDeleteUsers  # or -prod
python massDeleteUsers.py
```

**Interactive prompts**:
1. Path to filtered JSON file (from Step 1)
2. Review user count and preview of IDs
3. **Final confirmation: 'y' to delete (IRREVERSIBLE) or 'n' to cancel**
4. Watch deletion progress
5. Review summary of successes/failures

**Example output**:
```
New Relic User Deletion Script
============================================================
Loading API key...
✓ API key loaded successfully

Enter path to JSON file with user IDs: users_filtered.json

Loading user IDs from users_filtered.json...
✓ Loaded 9 unique user ID(s)

User IDs to be deleted:
  1. 1004371083
  2. 1004851935
  3. 1000474200
  ... and 6 more

Would you like to proceed with permanently deleting 9 user(s)? (y/n): y

Starting deletion process...

Deleting user 1/9: 1004371083... ✓ Success
Deleting user 2/9: 1004851935... ✓ Success
Deleting user 3/9: 1000474200... ✓ Success
...

============================================================
DELETION SUMMARY
============================================================
Total successful: 9
Total failed: 0
============================================================
```

---

## Environment-Specific Details

### Staging vs Production

The scripts are separated into two directories:

```
userDeleteOneMonth/
├── userDeleteOneMonth-staging/    # For staging-api.newrelic.com
│   ├── filterIds/
│   └── massDeleteUsers/
└── userDeleteOneMonth-prod/       # For api.newrelic.com
    ├── filterIds/
    └── massDeleteUsers/
```

**The ONLY difference** is the NerdGraph API endpoint:
- **Staging**: `https://staging-api.newrelic.com/graphql`
- **Production**: `https://api.newrelic.com/graphql`

**Best Practice**: 
1. Always test your complete workflow in staging first
2. Use staging to validate your filters and date thresholds
3. Only move to production after confirming staging results

---

## Input File Format Examples

### For filterOldUsers.py (Step 1)

Your input can be any JSON with user objects containing `id` and `created_at`:

```json
[
  {
    "full_name": "John Doe",
    "id": "1004371083",
    "email": "john@example.com",
    "created_at": 1669662687473,
    "user_tier": "full_user_tier"
  },
  {
    "full_name": "Jane Doe",
    "id": "1004851935",
    "email": "jane@example.com",
    "created_at": 1681848889518,
    "user_tier": "basic_user_tier"
  }
]
```

**Required fields**: `id`, `created_at` (Unix timestamp in milliseconds)

**Optional fields**: Everything else is ignored but can remain in the file

### For massDeleteUsers.py (Step 2)

Must be in this exact format (automatically created by filterOldUsers.py):

```json
{
  "userIds": [
    "1004371083",
    "1004851935",
    "1000474200"
  ]
}
```

---

## Troubleshooting

### filterOldUsers.py Issues

**"No valid user IDs found in JSON file"**
- Check that your JSON has an `id` field (or `userId`, `user_id`, etc.)
- Validate JSON syntax with a JSON validator
- Look at example file: `users.json.json`

**"No users found matching the criteria"**
- All users might be too recent (created within X days)
- Try a smaller days threshold
- Check that `created_at` timestamps are in milliseconds, not seconds

**"Users missing created date"**
- Your JSON might use a different field name than `created_at`
- The script looks for: `created_at`, `createdAt`, `dateCreated`, etc.
- Modify script if your field name is different

### massDeleteUsers.py Issues

**"API key not found"**
- Create `config/api_key.txt` with your API key
- Or set `NEWRELIC_API_KEY` environment variable
- Verify file permissions (should be readable)
- Check that there are no extra spaces or newlines in the key

**"Request failed" or timeout errors**
- Check internet connection
- Verify API key has user management permissions
- For large batches (100+ users), this is normal - script will continue
- Check New Relic API status page

**Partial failures in deletion**
- Some users may fail due to: SCIM management, active sessions, permission issues
- Review the failure summary at the end
- Failed user IDs can be manually investigated in New Relic UI
- Common failure: "User managed by SCIM cannot be deleted via API"

### General Issues

**"Invalid JSON format"**
- Use a JSON validator (jsonlint.com)
- Check for trailing commas
- Ensure proper quote marks (not smart quotes from Word/Docs)
- Verify file encoding is UTF-8

**Script hangs or freezes**
- Press Ctrl+C to cancel
- Check that input file isn't corrupted
- Try with a smaller test file first

---

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `config/api_key.txt` to `.gitignore`
   - Rotate keys after use if they're exposed

2. **Restrict API key permissions**
   - Use keys with minimum required permissions
   - Consider time-limited keys for one-off operations

3. **Audit trail**
   - Document when and why you ran the script
   - Save copies of input/output files
   - Record who authorized the deletion

4. **Test with small batches**
   - Run with 1-2 users first in staging
   - Verify deletion in UI before scaling up
   - Gradually increase batch sizes

---

## Example Real-World Workflow

**Scenario**: Accidental provisioning created 200 user records for `john.doe@example.com`

### Phase 1: Investigation (Staging)
```bash
# 0. First-time setup: Create venv and install dependencies
cd userDeleteOneMonth-staging/massDeleteUsers
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cd ..

# 1. Export user metadata to users_export.json

# 2. Filter to users older than 30 days
cd filterIds
python filterOldUsers.py
# Input: users_export.json
# Threshold: 30 days
# Output: users_export_filtered.json

# 3. Review filtered file
cat users_export_filtered.json
# Verify count: Should show ~200 user IDs

# 4. Test delete in staging (with just 2 IDs first)
cd ../massDeleteUsers
source venv/bin/activate  # Activate venv if not already active
# Edit users_export_filtered.json to only have 2 IDs
python massDeleteUsers.py
# Input: users_export_filtered.json
# Confirm: y

# 5. Verify in staging UI that 2 users are gone
```

### Phase 2: Production (After Staging Success)
```bash
# 6. Get approval from management/security

# 7. Setup prod venv (first time only)
cd userDeleteOneMonth-prod/massDeleteUsers
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cd ..

# 8. Export production user metadata to prod_users.json

# 9. Filter production users
cd filterIds
python filterOldUsers.py
# Input: prod_users.json
# Threshold: 30 days
# Output: prod_users_filtered.json

# 10. CRITICAL: Review every ID in prod_users_filtered.json

# 11. Execute deletion in small batches
cd ../massDeleteUsers
source venv/bin/activate  # Activate venv if not already active

# First batch: 10 users
python massDeleteUsers.py
# Verify in UI

# Second batch: 50 users
python massDeleteUsers.py
# Verify in UI

# Final batch: remaining 140 users
python massDeleteUsers.py
# Verify in UI

# 12. Document completion
# 13. Deactivate venv when done
deactivate
```

---

## When NOT to Use This Tool

- **Small batches** (< 10 users) - Manual deletion is safer and faster
- **Users you're unsure about** - Investigate first, delete later
- **Active users** - They might be legitimate, check with account owner
- **SCIM-managed users** - These require SCIM provider changes, not API deletion
- **Recent users** (< 7 days old) - May still be in provisioning, wait and verify first
- **Production without staging test** - Always test in staging first

---

## Support and Questions

For questions about:
- **New Relic user management**: See NerdGraph documentation
- **Script bugs or improvements**: Contact the script maintainer
- **Authorization to use this tool**: Contact your manager or security team

---

## File Structure Reference

```
userDeleteOneMonth/
├── README.md                                          # This file
│
├── userDeleteOneMonth-staging/
│   ├── filterIds/
│   │   ├── filterOldUsers.py                         # Step 1: Filter by date
│   │   ├── users.json.json                           # Example input
│   │   └── unfiltered.json                           # Example input
│   │
│   └── massDeleteUsers/
│       ├── massDeleteUsers.py                        # Step 2: Delete users
│       ├── example_users_dict.json                   # Example output from Step 1
│       ├── requirements.txt                          # Python dependencies
│       └── config/
│           └── api_key.txt                           # Your API key (gitignored)
│
└── userDeleteOneMonth-prod/
    ├── filterIds/
    │   ├── filterOldUsers.py                         # Step 1: Filter by date
    │   └── users.json.json                           # Example input
    │
    └── massDeleteUsers/
        ├── massDeleteUsers.py                        # Step 2: Delete users
        ├── example_users_dict.json                   # Example output from Step 1
        ├── requirements.txt                          # Python dependencies
        └── config/
            └── api_key.txt                           # Your API key (gitignored)
```

---

## Changelog

- **v1.0** - Initial release with two-script workflow
- Scripts support flexible JSON input formats
- Interactive prompts with confirmation steps
- Staging and production environment separation
