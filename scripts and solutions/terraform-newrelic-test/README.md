# New Relic Terraform Account Creation Test

This is a test template for troubleshooting Terraform plans with New Relic account creation. Technical support can use this as a starting point to reproduce and debug customer Terraform issues.

## Purpose

This template demonstrates:
- Basic New Relic provider configuration
- Creating a New Relic account using `newrelic_account_management` resource
- Proper variable handling for credentials

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) ~> 1.0 or higher
- New Relic User API Key with admin permissions
- Access to a New Relic parent account (partnership or organization account)

## Setup Instructions

### 1. Clone or Copy This Template

```bash
# If using from GitHub
git clone <repository-url>
cd terraform-newrelic-test

# Or simply copy this directory
```

### 2. Configure Credentials

Copy the example variables file and add your credentials:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your actual values:
```hcl
new_relic_api_key    = "NRAK-YOUR_ACTUAL_API_KEY"
new_relic_account_id = "YOUR_PARENT_ACCOUNT_ID"
```

**Important:**
- Use a User API Key (starts with `NRAK-`), not an Ingest or License key
- The account ID should be your partnership or parent organization account
- `terraform.tfvars` is gitignored and will not be committed

### 3. Initialize Terraform

```bash
terraform init
```

This downloads the New Relic provider and prepares the working directory.

### 4. Review the Plan

```bash
terraform plan
```

Review what Terraform will create. You should see:
- One `newrelic_account_management` resource to be created
- The account name and region configuration

### 5. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted to create the account.

### 6. Verify Creation

After successful apply:
- Check the output for the new account ID
- Verify in New Relic UI: Settings → Administration → Accounts
- Note: New accounts may take a few moments to appear in the UI

### 7. Clean Up

To remove the test account:

```bash
terraform destroy
```

Type `yes` when prompted.

## Files Overview

- `main.tf` - Main configuration with provider and resource definitions
- `variables.tf` - Variable declarations for credentials
- `terraform.tfvars.example` - Template for credentials (copy to `terraform.tfvars`)
- `terraform.tfvars` - Your actual credentials (gitignored, not committed)

## Customization for Testing

### Change Account Name

In `main.tf`, modify the `name` attribute:
```hcl
resource "newrelic_account_management" "test_account" {
  name   = "Your Custom Account Name"
  region = "us01"
}
```

### Change Region

Valid regions:
- `us01` - US data center (default)
- `eu01` - EU data center

Update both the provider `region` parameter and the resource `region` attribute.

## Common Issues

### Authentication Errors

**Error:** `401 Unauthorized` or `Invalid API key`

**Solutions:**
- Verify you're using a User API Key (starts with `NRAK-`)
- Check the key has not expired
- Ensure the key has admin permissions
- Confirm you're using the correct region (US vs EU)

### Account Creation Fails

**Error:** `Error creating account` or `403 Forbidden`

**Solutions:**
- Verify the parent account ID is a partnership or organization account
- Confirm your user has permission to create sub-accounts
- Check you haven't exceeded account creation limits

### Region Mismatch

**Error:** `Error: Invalid region`

**Solutions:**
- Ensure provider `region` matches resource `region`
- Use lowercase: `us01` not `US01`
- Valid values: `us01` or `eu01`

## Troubleshooting Tips

1. **Enable debug logging:**
   ```bash
   export TF_LOG=DEBUG
   terraform apply
   ```

2. **Verify provider version:**
   ```bash
   terraform version
   ```

3. **Reinitialize if provider issues occur:**
   ```bash
   rm -rf .terraform .terraform.lock.hcl
   terraform init
   ```

4. **Check state file for actual created resources:**
   ```bash
   terraform show
   ```

## Additional Resources

- [New Relic Terraform Provider Documentation](https://registry.terraform.io/providers/newrelic/newrelic/latest/docs)
- [Account Management Resource](https://registry.terraform.io/providers/newrelic/newrelic/latest/docs/resources/account_management)
- [New Relic API Keys Documentation](https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/)

## Support

For New Relic-specific Terraform issues, refer to:
- [Provider GitHub Issues](https://github.com/newrelic/terraform-provider-newrelic/issues)
- New Relic Support (for account and API key issues)
