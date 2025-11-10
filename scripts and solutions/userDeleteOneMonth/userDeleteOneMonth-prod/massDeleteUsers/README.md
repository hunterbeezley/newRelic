# New Relic User Deletion Script

A safe, production-ready Python script for bulk deletion of New Relic users via the NerdGraph API.

## Features

- ✅ **Security**: API key stored separately from code
- ✅ **Safety**: Mandatory user confirmation before deletions
- ✅ **Scalability**: Handles thousands of user IDs efficiently
- ✅ **Error Handling**: Comprehensive error handling with detailed feedback
- ✅ **Flexibility**: Supports multiple JSON formats
- ✅ **User-Friendly**: Clear progress indicators and summary reports

## Prerequisites

- Python 3.6+
- `requests` library

## Installation

1. Install required dependencies:
```bash
pip install requests
```

2. Set up your API key (choose one method):

### Option A: Config File (Recommended)
Create `config/api_key.txt` in the same directory as the script:
```bash
echo "YOUR_NEWRELIC_API_KEY_HERE" > config/api_key.txt
```

### Option B: Home Directory
Create `~/.newrelic/api_key.txt`:
```bash
mkdir -p ~/.newrelic
echo "YOUR_NEWRELIC_API_KEY_HERE" > ~/.newrelic/api_key.txt
```

### Option C: Environment Variable
```bash
export NEWRELIC_API_KEY="YOUR_NEWRELIC_API_KEY_HERE"
```

## Usage

1. Make the script executable (optional):
```bash
chmod +x delete_users.py
```

2. Run the script:
```bash
python delete_users.py
```

3. Follow the prompts:
   - Enter the path to your JSON file containing user IDs
   - Review the number of users to be deleted
   - Confirm deletion with 'y' or cancel with 'n'
   - View real-time progress and results
   - Optionally process another file

## JSON File Formats

The script supports multiple JSON formats:

### Format 1: Simple Array
```json
[
  "user-id-1",
  "user-id-2",
  "user-id-3"
]
```

### Format 2: Object with userIds Key
```json
{
  "userIds": [
    "user-id-1",
    "user-id-2",
    "user-id-3"
  ]
}
```

### Format 3: Object with users Key
```json
{
  "users": [
    "user-id-1",
    "user-id-2",
    "user-id-3"
  ]
}
```

### Format 4: Single User
```json
{
  "userId": "user-id-1"
}
```

## Example Output

```
New Relic User Deletion Script
============================================================
Loading API key...
✓ API key loaded successfully

Enter path to JSON file with user IDs: users_to_delete.json

Loading user IDs from users_to_delete.json...
✓ Loaded 3 unique user ID(s)

User IDs to be deleted:
  1. user-id-1
  2. user-id-2
  3. user-id-3

Would you like to proceed with permanently deleting 3 user(s)? (y/n): y

Starting deletion process...

Deleting user 1/3: user-id-1... ✓ Success
Deleting user 2/3: user-id-2... ✓ Success
Deleting user 3/3: user-id-3... ✓ Success

============================================================
DELETION SUMMARY
============================================================
Total successful: 3
Total failed: 0
============================================================

Would you like to run this again for a new JSON file? (y/n): n
Exiting.
```

## Error Handling

The script handles various error scenarios:

- **Invalid JSON**: Clear error messages for malformed JSON files
- **Missing Files**: Friendly notification if JSON file not found
- **API Errors**: Detailed error messages from NerdGraph API
- **Network Issues**: Timeout and connection error handling
- **Duplicate IDs**: Automatically deduplicates user IDs
- **Invalid API Keys**: Clear instructions on how to configure

### Example Error Output

```
Deleting user 1/5: invalid-user-id... ✗ Failed: User not found
Deleting user 2/5: user-id-2... ✓ Success
...

============================================================
DELETION SUMMARY
============================================================
Total successful: 4
Total failed: 1

Failed deletions:
  - User ID: invalid-user-id
    Error: User not found
============================================================
```

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `config/api_key.txt` to your `.gitignore`
   - Use environment variables in CI/CD pipelines

2. **Restrict API key permissions**
   - Use keys with minimum required permissions
   - Rotate keys regularly

3. **Audit trail**
   - Keep logs of deletion operations
   - Review the summary before processing large batches

4. **Test first**
   - Test with a small batch of users first
   - Verify users are actually deleted in New Relic UI

## Scalability

The script is designed to handle large batches efficiently:

- **Thousands of users**: Processes sequentially with progress updates
- **Memory efficient**: Streams data and processes one user at a time
- **Timeout handling**: 30-second timeout per API call
- **Resumable**: Can re-run with remaining user IDs if issues occur

## Troubleshooting

### "API key not found" Error
- Ensure `config/api_key.txt` exists with your valid API key
- Check file permissions (should be readable)
- Try using environment variable method instead

### "Invalid JSON format" Error
- Validate your JSON file using a JSON validator
- Ensure the file uses one of the supported formats
- Check for trailing commas or syntax errors

### Network/Timeout Errors
- Check your internet connection
- Verify the New Relic API endpoint is accessible
- Try reducing batch size if processing many users

### Rate Limiting
- New Relic may have rate limits on the NerdGraph API
- Add delays between requests if needed (modify the script)
- Contact New Relic support for rate limit information

## Contributing

Suggestions for improvements:
- Add batch processing with configurable delays
- Add dry-run mode to preview without deleting
- Export failed deletions to a CSV file
- Add logging to file for audit purposes

## License

This script is provided as-is for use with New Relic's NerdGraph API.

## Support

For New Relic API issues, consult:
- [New Relic NerdGraph Documentation](https://docs.newrelic.com/docs/apis/nerdgraph/)
- [New Relic Support](https://support.newrelic.com/)

## Warning

⚠️ **This script permanently deletes users from New Relic. This action cannot be undone.**

Always:
- Review the list of users before confirming deletion
- Test with a small batch first
- Have backups of user data if needed
- Ensure you have proper authorization to delete users
