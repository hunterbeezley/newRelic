# New Relic Bulk User Email Update

***NOTE: this code is not owned or maintained by New Relic. All outcomes of this script are the sole responsibility of those who use it.***

This Python script allows you to update the email address of one or multiple users in your New Relic account using the New Relic User Management API.

## How to Use

1. Before using this script, you must have a New Relic account and generate an API key for your account. To generate an API key, please follow the instructions in the [New Relic documentation](https://docs.newrelic.com/docs/apis/get-started/intro-apis/types-new-relic-api-keys#admin).

2. Save the user ID and new email address for each user you wish to update in a CSV file. The CSV file should have two columns: 'ID' and 'Email'.

3. Run the script by executing the following command in your terminal or command prompt:

    ```
    python newrelic_user_management.py
    ```

4. You will be prompted to enter your New Relic API key and the path to the CSV file.

5. The script will loop through each row in the CSV file and update the email address of each user.

6. If there are errors in the response from the New Relic User Management API, the script will print out the error messages. If the update is successful, the script will print out a success message for each user ID that has been updated.

## Requirements

- Python 3.x
- `requests` module: You can install this module by running `pip install requests` in your terminal or command prompt.
