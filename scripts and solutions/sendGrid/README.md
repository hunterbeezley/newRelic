# SendGrid Tool - Quick Reference Cheat Sheet
---

## First Time Setup (Once)

```bash
cd YOUR/PATH/HERE
./setup.sh
```

Follow the prompts. Get API keys from 1Password GTS vault.

---

## Daily Commands

**Navigate to the tool directory first:**
```bash
cd YOUR/PATH/HERE
```

### Test Connections
```bash
./run.sh test
```

### Check if Email is Suppressed
```bash
./run.sh check user@example.com
```

### Remove Single Email

**Dry run first (preview):**
```bash
./run.sh remove --email user@example.com --dry-run
```

**Execute removal:**
```bash
./run.sh remove --email user@example.com
```

### Remove Multiple Emails from CSV

**Dry run first:**
```bash
./run.sh remove --csv emails.csv --dry-run
```

**Execute removal:**
```bash
./run.sh remove --csv emails.csv
```

### Remove All Emails from Domain

**Dry run first:**
```bash
./run.sh remove --domain @newrelic.com --dry-run
```

**Execute removal:**
```bash
./run.sh remove --domain @newrelic.com
```

---

## Important Flags

| Flag | What it does |
|------|-------------|
| `--dry-run` | - previews changes without executing |
| `--lists <list1> <list2>` | Target specific lists (bounces, blocks, spam_reports, etc.) |
| `--no-confirm` | Skip confirmation prompt (automation mode) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SSL errors | Run `./setup.sh` to configure SSL certificates (macOS only) |
| Connection failed | Run `./run.sh test` to check API keys |
| Script not found | Make sure you're in the sendGrid directory |
| Permission denied | Run `chmod +x setup.sh run.sh` |

---

## View Logs
```bash
ls -t logs/*.log | head -1 | xargs cat
```

---

## CSV File Format

Create `emails.csv` like this:
```csv
email
user1@example.com
user2@example.com
user3@example.com
```

---

## Help Commands

```bash
# Setup help
./setup.sh

# Run help
./run.sh

# Remove suppressions help
./run.sh remove --help
```

---

## Note:

- **SSL configured automatically on macOS** (setup.sh extracts certificates)
- **Tool checks all 7 accounts automatically**
- **Logs saved to `logs/` directory**
- **Get API keys from 1Password GTS vault**

---


