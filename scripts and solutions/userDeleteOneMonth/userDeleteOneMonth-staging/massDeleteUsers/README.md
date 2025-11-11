# userDeleteOneMonth

A script that takes in a .json file of user ID's and executes a Nerdgraph API mutation to delete each one. 

Note: This script was intended to be run after first running 'filterOldUsers.py' which takes in a json of user metadata, filters results to a threshold in x days and then provides a filtered.json to be provided in THIS script. If you choose to not run filterOldUsers.py, ensure the the .json for THIS script is in the following format:
```
{
  "userIds": [
    "user-id-1",
    "user-id-2",
    "user-id-3"
  ]
}
```

## Warning

⚠️ **This script permanently deletes users from New Relic. This action cannot be undone.**

Always:
- Review the list of users before confirming deletion
- Test with a small batch first
- Have backups of user data if needed
- Ensure you have proper authorization to delete users

## pre-req's

- Python 3.6+
- `requests` library

## Install

1. dependencies:
```bash
pip install requests
```

2. Set up API key:

###  Config File (Recommended)
Create `config/api_key.txt` in the same directory as the script:
```bash
echo "YOUR_NEWRELIC_API_KEY_HERE" > config/api_key.txt
```


## Run

1. Run the script:
```bash
python delete_users.py
```

2. Follow the prompts:
   - Enter the path to your JSON file containing user IDs
   - Review the number of users to be deleted
   - Confirm deletion with 'y' or cancel with 'n'
   - See results
   - Optionally process another file

## JSON File Formats


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

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `config/api_key.txt` to your `.gitignore`
   - Use environment variables in CI/CD pipelines

2. **Test first**
   - Test with a small batch of test users first
   - Verify users are actually deleted in New Relic UI

## Scalability

The script should be able to handle very large batches

## Troubleshootin'

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


