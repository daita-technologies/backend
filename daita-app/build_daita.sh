#!/bin/bash


### load config file
. "$1"

OUTPUT_BUILD_DAITA=$2
OUTPUT_FE_CONFIG=$3

### load output of daita-app 
. "$OUTPUT_BUILD_DAITA"


cd daita-app


parameters_override="Mode=${MODE} Stage=${DAITA_STAGE} Application=${DAITA_APPLICATION} 
                    SecurityGroupIds=${SECURITY_GROUP_IDS} SubnetIDs=${SUB_NET_IDS} 
                    S3BucketName=${DAITA_S3_BUCKET} 
                    EFSFileSystemId=${EFS_ID} 
                    MaxConcurrencyTasks=${MAX_CONCURRENCY_TASK} 
                    ROOTEFS=${ROOT_EFS} 
                    DomainUserPool=${DOMAIN_USER_POOL} 
                    VPCid=${VPC_ID} 
                    LogoutUrl=${LOG_OUT_URL} 
                    CertificateUserpoolDomain=${CERTIFICATE_USERPOLL_DOMAIN} 
                    S3AnnoBucket=${ANNO_S3_BUCKET} 
                    PublicSubnetOne=${PublicSubnetOne} 
                    PublicSubnetTwo=${PublicSubnetTwo} 
                    ContainerSecurityGroup=${ContainerSecurityGroup} 
                    VPC=${VPC} 
                    VPCEndpointSQSDnsEntries=${VPCEndpointSQSDnsEntries}
                    TokenOauth2BotSlackFeedBack=${OAUTH2BOT_SLACK_FEED_BACK}"

sam build
sam deploy --no-confirm-changeset --disable-rollback \
        --resolve-image-repos --config-env $DAITA_STAGE \
        --stack-name "$DAITA_STAGE-${DAITA_APPLICATION}-app" \
        --s3-prefix "$DAITA_STAGE-${DAITA_APPLICATION}-app" \
        --region $AWS_REGION \
        --parameter-overrides $parameters_override | tee output.txt


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
        
        first_line=$value
        is_first_line_value=true
    else
        if [[ "$line" =~ .*"-------".* ]]; then
            echo "skip line"
        else
            if [ "$is_first_line_value" = true ]; then
                final_line=$first_line$line                
                dict_output[$key]=$final_line
                is_first_line_value=false
            fi
        fi
    fi
done < $filename

DecompressEcrRepositoryName=${dict_output["DecompressEcrRepositoryName"]}
CompressDownloadEcrRepositoryName=${dict_output["CompressDownloadEcrRepositoryName"]}
CognitoUserPoolRef=${dict_output["CognitoUserPoolRef"]}
CognitoIdentityPoolIdRef=${dict_output["CognitoIdentityPoolIdRef"]}
CommonCodeLayerRef=${dict_output["CommonCodeLayerRef"]}
TableDaitaProjectsName=${dict_output["TableDaitaProjectsName"]}
TableDaitaDataOriginalName=${dict_output["TableDaitaDataOriginalName"]}
TableUserName=${dict_output["TableUserName"]}
### for lambda functions
SendEmailIdentityIDFunction=${dict_output["SendEmailIdentityIDFunction"]}
### export for FE config
ApiDaitaAppUrl=${dict_output["ApiDaitaAppUrl"]}
ApiAuthDaitaUrl=${dict_output["ApiAuthDaitaUrl"]}
CognitoAppIntegrateID=${dict_output["CognitoAppIntegrateID"]}


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
echo "CognitoUserPoolRef=$CognitoUserPoolRef" >> $OUTPUT_BUILD_DAITA
echo "CognitoIdentityPoolIdRef=$CognitoIdentityPoolIdRef" >> $OUTPUT_BUILD_DAITA
echo "CommonCodeLayerRef=$CommonCodeLayerRef" >> $OUTPUT_BUILD_DAITA
echo "TableDaitaProjectsName=$TableDaitaProjectsName" >> $OUTPUT_BUILD_DAITA
echo "TableDaitaDataOriginalName=$TableDaitaDataOriginalName" >> $OUTPUT_BUILD_DAITA
echo "TableUserName=$TableUserName" >> $OUTPUT_BUILD_DAITA
echo "SendEmailIdentityIDFunction=$SendEmailIdentityIDFunction" >> $OUTPUT_BUILD_DAITA



###========= SAVE FE CONFIG ===============
echo "REACT_APP_AUTH_API_URL=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_INVITE_API_URL=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_PROJECT_API_URL=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_GENERATE_API_URL=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_HEALTH_CHECK_API_URL=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_DOWNLOAD_ZIP_API=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_UPLOAD_ZIP_API=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_TASK_API_URL=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_CREATE_PROJECT_SAMPLE=$ApiDaitaAppUrl" >> $OUTPUT_FE_CONFIG

echo "REACT_APP_S3_BUCKET_NAME=$DAITA_S3_BUCKET" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_S3_REGION=$AWS_REGION" >> $OUTPUT_FE_CONFIG

echo "REACT_APP_RECAPTCHA_SITE_KEY=6LcqEGMeAAAAAAEDnBue7fwR4pmvNO7JKWkHtAjl" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_API_AMAZON_COGNITO=https://${DOMAIN_USER_POOL}/oauth2/authorize" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_COGNITO_REDIRECT_URI=${ApiAuthDaitaUrl}/auth/login_social" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_COGNITO_CLIENTID=${CognitoAppIntegrateID}" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_API_LOGOUT_SOCIAL=https://${DOMAIN_USER_POOL}/logout?client_id=${CognitoAppIntegrateID}" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_GITHUB_IDENTITY_PROVIDER=github" >> $OUTPUT_FE_CONFIG

echo "REACT_APP_FEEDBACK_SLACK=${ApiDaitaAppUrl}/webhook/client-feedback" >> $OUTPUT_FE_CONFIG
echo "REACT_APP_PRESIGN_URL_UPLOAD_FEEDBACK_IMAGE=${ApiDaitaAppUrl}/feedback/presign_url_image" >> $OUTPUT_FE_CONFIG