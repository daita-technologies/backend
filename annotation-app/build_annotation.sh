### load config file
. "$1"

OUTPUT_BUILD_DAITA=$2

### load output of daita-app 
. "$OUTPUT_BUILD_DAITA"



cd annotation-app

parameters_override="Stage=${ANNOTATION_STAGE} Application=${ANNO_APPLICATION} 
                    S3AnnoBucketName=${ANNO_S3_BUCKET} EFSFileSystemId=${EFS_ID}
                    CommonCodeLayerRef=${CommonCodeLayerRef} CognitoUserPoolRef=${CognitoUserPoolRef} 
                    CognitoIdentityPoolIdRef=${CognitoIdentityPoolIdRef}
                    TableDaitaProjectsName=${TableDaitaProjectsName}
                    TableDaitaDataOriginalName=${TableDaitaDataOriginalName} 
                    S3DaitaBucketName=${DAITA_S3_BUCKET}"

sam build --template-file template_annotation_app.yaml
sam deploy --template-file template_annotation_app.yaml --no-confirm-changeset --disable-rollback \
            --config-env $ANNOTATION_STAGE \
            --resolve-image-repos --resolve-s3 \
            --stack-name "$ANNOTATION_STAGE-$ANNO_APPLICATION-app" \
            --s3-prefix "$ANNOTATION_STAGE-$ANNO_APPLICATION-app" \
            --region $AWS_REGION \
            --parameter-overrides $parameters_override | tee output.txt