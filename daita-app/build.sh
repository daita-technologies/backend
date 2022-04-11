#!/bin/bash

STAGE="dev"

###=== AWS config ======
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="366577564432"


sam build
sam deploy --no-confirm-changeset --disable-rollback --config-env $STAGE | tee output.txt
output=$(cat output.txt)
echo =========================================
output=$(echo $output)

echo @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
echo Get value of ecr

shopt -s extglob


keyname="DecompressEcrRepositoryName"
a=$output
[[ $a =~ Key[[:space:]]$keyname[[:space:]].+Key ]]
a=${BASH_REMATCH[0]}
[[ $a =~ Value.+Key ]]
a=${BASH_REMATCH[0]}
[[ $a =~ [[:space:]].+[[:space:]] ]]
a=${BASH_REMATCH[0]}
### strip space
a=${a##*( )}
a=${a%%*( )}

###=== ECR config=========
IMAGE_REPO_NAME=$a
IMAGE_TAG="latest"

### Login to ecr
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

### Build image
cd ./dataflow-service/tasks/decompress
docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG

### Push image to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG



