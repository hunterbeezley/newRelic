terraform {
  required_version = "~> 1.0"
  required_providers {
    newrelic = {
      source  = "newrelic/newrelic"
      version = "~> 3.0"
    }
  }
}

# Configure the New Relic provider
provider "newrelic" {
  api_key    = var.new_relic_api_key
  account_id = var.new_relic_account_id
  region     = "US" # Change to "EU" for EU data center
}

# Create a test account
# Note: Requires a partnership or organization parent account
resource "newrelic_account_management" "test_account" {
  name   = "Terraform Test Account"
  region = "us01" # us01 for US, eu01 for EU
}
