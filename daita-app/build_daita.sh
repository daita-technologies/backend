#!/bin/bash


AWS_REGION=$1
AWS_ACCOUNT_ID=$2
STAGE=$3
OUTPUT_BUILD_DAITA=$4

# func_extract_value_of_key () {
#     output_para=$1
#     keyname_find=$2
#     keyname_prev_pos=$3
    
#     a=$output_para
#     [[ $a =~ Key[[:space:]]$keyname_find[[:space:]].+$keyname_prev_pos ]]
#     a=${BASH_REMATCH[0]}
#     [[ $a =~ Value.+Key ]]
#     a=${BASH_REMATCH[0]}
#     [[ $a =~ [[:space:]].+[[:space:]] ]]
#     a=${BASH_REMATCH[0]}
#     ### strip space
#     a=${a##*( )}
#     a=${a%%*( )}
    
#     echo "$a"
# }

cd daita-app

sam build
sam deploy --no-confirm-changeset --disable-rollback --config-env $STAGE | tee output.txt


echo @@@@@@@@@@@@@@@@@@@@@@@@ Upload docker to ECR ==========

shopt -s extglob

declare -A dict_output
filename="output.txt"

while read line; do
    # reading each line
    if [[ "$line" =~ "Key".+ ]]; then

        [[ "$line" =~ [[:space:]].+ ]]
        a=${BASH_REMATCH[0]}
        a=${a##*( )}
        a=${a%%*( )}
        key=$a
    fi
    if [[ "$line" =~ "Value".+ ]]; then
        [[ "$line" =~ [[:space:]].+ ]]
        value=${BASH_REMATCH[0]}
        value=${value##*( )}
        value=${value%%*( )}
        dict_output[$key]=$value
    fi
done < $filename

DecompressEcrRepositoryName=${dict_output["DecompressEcrRepositoryName"]}
CompressDownloadEcrRepositoryName=${dict_output["CompressDownloadEcrRepositoryName"]}
CognitoUserPoolRef=${dict_output["CognitoUserPoolRef"]}
CognitoIdentityPoolIdRef=${dict_output["CognitoIdentityPoolIdRef"]}
CommonCodeLayerRef=${dict_output["CommonCodeLayerRef"]}
TableDaitaProjectsName=${dict_output["TableDaitaProjectsName"]}
TableDaitaDataOriginalName=${dict_output["TableDaitaDataOriginalName"]}

###=== ECR config=========
IMAGE_REPO_NAME=$DecompressEcrRepositoryName
IMAGE_TAG="latest"

### Login to ecr
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

### Build image for decompress
cd ./dataflow-service/decompress-upload-app/tasks/decompress
docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG

### Push image to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG

###=== ECR config=========
IMAGE_REPO_NAME1=$CompressDownloadEcrRepositoryName
IMAGE_TAG1="latest"
echo build $IMAGE_REPO_NAME1
cd ..
cd ..
cd ..
pwd
cd ./compress-download-app/tasks/download
pwd
docker build -t $IMAGE_REPO_NAME1:$IMAGE_TAG1 .
docker tag $IMAGE_REPO_NAME1:$IMAGE_TAG1 $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME1:$IMAGE_TAG1

### Push image to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_REPO_NAME1:$IMAGE_TAG1


###======= Store output to file ==========
echo "CognitoUserPoolRef=$CognitoUserPoolRef" > $OUTPUT_BUILD_DAITA
echo "CognitoIdentityPoolIdRef=$CognitoIdentityPoolIdRef" >> $OUTPUT_BUILD_DAITA
echo "CommonCodeLayerRef=$CommonCodeLayerRef" >> $OUTPUT_BUILD_DAITA
echo "TableDaitaProjectsName=$TableDaitaProjectsName" >> $OUTPUT_BUILD_DAITA
echo "TableDaitaDataOriginalName=$TableDaitaDataOriginalName" >> $OUTPUT_BUILD_DAITA
