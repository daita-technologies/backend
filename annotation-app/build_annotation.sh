#!/bin/bash

AWS_REGION=$1
AWS_ACCOUNT_ID=$2
STAGE=$3
OUTPUT_BUILD_DAITA=$4


### load output of daita-app 
. "$OUTPUT_BUILD_DAITA"

cd annotation-app

parameters_override="Stage=${STAGE} Application=anno 
                    S3BucketName=client-annotation-bucket EFSFileSystemId=fs-0199771f2dfe97ace 
                    CommonCodeLayerRef=${CommonCodeLayerRef} CognitoUserPoolRef=${CognitoUserPoolRef} 
                    CognitoIdentityPoolIdRef=${CognitoIdentityPoolIdRef}"

sam build --template-file template_annotation_app.yaml
sam deploy --template-file template_annotation_app.yaml --no-confirm-changeset --disable-rollback --config-env $STAGE \
    --parameter-overrides $parameters_override | tee output.txt
