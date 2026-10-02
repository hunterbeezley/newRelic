# Output the created account ID for verification
output "account_id" {
  description = "The ID of the newly created New Relic account"
  value       = newrelic_account_management.test_account.id
}

output "account_name" {
  description = "The name of the newly created New Relic account"
  value       = newrelic_account_management.test_account.name
}
