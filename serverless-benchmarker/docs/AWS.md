# Amazon Web Services (aws)

* [AWS Console](https://console.aws.amazon.com/)

## Setup

1. Sign up for an AWS account: https://aws.amazon.com/free
2. Open the `Users` page under Identity & Access Management (IAM): https://console.aws.amazon.com/iam/home#/users
3. Click on `Add user`, enter a username (e.g., `sb-admin`), and enable `Programmatic access`.
4. On the next page, choose `Attach existing policies directly` and enable `AdministratorAccess`.
5. Confirm everything by clicking `Create user`
6. Copy the `Access key ID` and  `Secret access key` to a safe place.
7. Run `sb login aws` and enter your access and secret key to authenticate.

For more detailed instructions, checkout the credentials documentation of the [Serverless Framework](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/).
