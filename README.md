# GenAI Examples

This repository contains a collection of Generative AI (GenAI) examples, showcasing practical applications, code samples, and best practices for building GenAI-powered solutions. The examples are designed to help developers, data scientists, and AI enthusiasts get started quickly with GenAI on AWS.

## Prerequisites

Before running any examples in this repository, you need to set up your AWS environment. Follow these steps to get started:

### 1. Create an AWS Account
- Visit [https://aws.amazon.com/](https://aws.amazon.com/) and sign up for a new AWS account if you do not already have one.

### 2. Set Up AWS Organizations
- AWS Organizations allows you to centrally manage billing, compliance, and access across multiple AWS accounts.
- In the AWS Console, search for **Organizations** and follow the prompts to create an organization.
- You can add additional accounts as needed for development, production, etc.

### 3. Enable AWS Identity Center (formerly AWS SSO)
- In the AWS Console, search for **IAM Identity Center** (or **AWS SSO**).
- Click **Enable** to activate Identity Center for your organization.
- Configure your Identity Center directory (choose AWS-managed or connect to an external identity provider).

### 4. Create a User in Identity Center
- In the Identity Center dashboard, go to **Users** and click **Add user**.
- Enter the user's details (name, email, etc.) and assign them to the appropriate group or permission set (e.g., AdministratorAccess for full access).
- The user will receive an email invitation to set up their account.

### 5. Enable Local Development Access (SSO Setup)
- Install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) if you haven't already.
- Run the following command to configure SSO for your development profile:

  ```sh
  aws configure sso
  ```
- Follow the prompts to enter your SSO start URL, region, and profile name (e.g., `dev`).
- To authenticate and obtain credentials for your session, run:

  ```sh
  aws sso login --profile dev
  ```
- You are now ready to use the AWS CLI and SDKs with your SSO-authenticated profile.

## Example Structure

Each example in this repository is organized in its own subdirectory, with clear instructions and code samples. Examples may include:
- Jupyter notebooks
- Python scripts
- Infrastructure-as-Code templates
- Integration samples with AWS services (e.g., Bedrock, Lambda, S3)

## Contributing

Contributions are welcome! Please open issues or pull requests to suggest new examples or improvements.

## License

See the root `LICENSE` file for license information.

## Support

For questions or issues, please refer to the main repository or open an issue.
