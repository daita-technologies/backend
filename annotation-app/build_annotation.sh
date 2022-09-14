#!/bin/bash

### load config file
. "$1"

echo $DAITA_S3_BUCKET

### load output of daita-app 
. "$OUTPUT_BUILD_DAITA"

cd annotation-app

parameters_override="Stage=${ANNOTATION_STAGE} Application=anno 
                    S3AnnoBucketName=${ANNO_S3_BUCKET} EFSFileSystemId=fs-0199771f2dfe97ace 
                    CommonCodeLayerRef=${CommonCodeLayerRef} CognitoUserPoolRef=${CognitoUserPoolRef} 
                    CognitoIdentityPoolIdRef=${CognitoIdentityPoolIdRef}
                    TableDaitaProjectsName=${TableDaitaProjectsName}
                    TableDaitaDataOriginalName=${TableDaitaDataOriginalName} 
                    S3DaitaBucketName=${DAITA_S3_BUCKET}"

sam build --template-file template_annotation_app.yaml
sam deploy --template-file template_annotation_app.yaml --no-confirm-changeset --disable-rollback \
            --config-env $ANNOTATION_STAGE \
            --parameter-overrides $parameters_override | tee output.txt
