### load config file
. "$1"

OUTPUT_BUILD_DAITA=$2
OUTPUT_FE_CONFIG=$3

### load output of daita-app 
. "$OUTPUT_BUILD_DAITA"



cd annotation-app

parameters_override="Stage=${ANNOTATION_STAGE} Application=${ANNO_APPLICATION} 
                    S3AnnoBucketName=${ANNO_S3_BUCKET} EFSFileSystemId=${EFS_ID}
                    CommonCodeLayerRef=${CommonCodeLayerRef} CognitoUserPoolRef=${CognitoUserPoolRef} 
                    CognitoIdentityPoolIdRef=${CognitoIdentityPoolIdRef}
                    TableDaitaProjectsName=${TableDaitaProjectsName}
                    TableDaitaDataOriginalName=${TableDaitaDataOriginalName} 
                    S3DaitaBucketName=${DAITA_S3_BUCKET}
                    PublicSubnetOne=${PublicSubnetOne}
                    PublicSubnetTwo=${PublicSubnetTwo}
                    ContainerSecurityGroup=${ContainerSecurityGroup}
                    VPC=${VPC}
                    VPCEndpointSQSDnsEntries=${VPCEndpointSQSDnsEntries}
                    EFSFileSystemId=${EFSFileSystemId}
                    EFSAccessPoint=${EFSAccessPoint}
                    EFSAccessPointArn=${EFSAccessPointArn}"

sam build --template-file template_annotation_app.yaml
sam deploy --template-file template_annotation_app.yaml --no-confirm-changeset --disable-rollback \
            --config-env $ANNOTATION_STAGE \
            --resolve-image-repos --resolve-s3 \
            --stack-name "$ANNOTATION_STAGE-$ANNO_APPLICATION-app" \
            --s3-prefix "$ANNOTATION_STAGE-$ANNO_APPLICATION-app" \
            --region $AWS_REGION \
            --parameter-overrides $parameters_override | tee output_anno.txt

### Read output from template
shopt -s extglob

declare -A dict_output
filename="output_anno.txt"

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

ApiAnnoAppUrl=${dict_output["ApiAnnoAppUrl"]}


###========= SAVE FE CONFIG ===============
echo "REACT_APP_ANNOTATION_PROJECT_API=$ApiAnnoAppUrl" >> $OUTPUT_FE_CONFIG