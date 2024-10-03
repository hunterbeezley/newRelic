This tool is for performing User Asset Migrations. 
The script compares a TSV of users (retrieved from the NR userManagement UI before running the migration) against the JSON of the migration results.

The script takes in the path of each file, parses the content to find exact matching srrings of the "ID" from the TSV and the "users_migrated": array from the JSON.

This script will be helpful for particularly large asset migrations. 

As a best practice, still compare by eyesight (or via numbers, sheets, etc.) in the event the script has an unexpected bug. But as of writing this ReadMe, the tool seems to compare correctly.
