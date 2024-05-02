# New Relic Deployment Markers for Multiple GUID's

This script allows you to execute GraphQL mutations for a list of GUIDs provided in a CSV file using the New Relic GraphQL API.

***NOTE: this code is not owned or maintained by New Relic. All outcomes of this script are the sole responsibility of those who use it.***

## Prerequisites

- Python 3.x installed
- Required Python packages installed. Install them using pip:

## Usage

1. Clone this repository to your local machine or download the script file.

2. Ensure you have a CSV file (`guids.csv`) with the GUIDs in the same directory as the script or provide the correct path to your CSV file in the script.

3. Open the script and replace `'YOUR_NEW_RELIC_USER_KEY'` with your actual New Relic user key.

4. Run the script:

The script will read each GUID from the CSV file and execute a GraphQL mutation for each GUID using the specified endpoint and mutation template.

## Customization

- If needed, modify the GraphQL mutation template (`MUTATION_TEMPLATE`) to suit your specific mutation requirements.

- Update the CSV file path (`CSV_FILE_PATH`) if your CSV file is located in a different directory or has a different name.
