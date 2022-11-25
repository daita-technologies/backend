1. Copy and replace env in [daita-app/samconfig.toml] , do not change the config inside
[dev.deploy.parameters]
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket-eu58g5l8is1s"
confirm_changeset = true
capabilities = "CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM"
disable_rollback = true
image_repositories = []

2. Copy and replace env in [annotation-app/samconfig.toml] , do not change the config inside
[dev.deploy.parameters]
confirm_changeset = true
capabilities = "CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM"
disable_rollback = true
image_repositories = []

3. replace dev env trong [main_config.cnf]
DAITA_STAGE=dev
ANNOTATION_STAGE=dev

4. Use `bash main_build.sh` to build full flow.
