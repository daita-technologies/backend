#!/bin/bash


### load config file
. "$1"

OUTPUT_BUILD_DAITA=$2
OUTPUT_FE_CONFIG=$3


cd infrastructure-def-app


parameters_override="Mode=${MODE} Stage=${DAITA_STAGE} Application=${INFRA_APPLICATION}"

sam build --template-file template_infra.yaml
sam deploy --template-file template_infra.yaml --no-confirm-changeset --disable-rollback \
        --resolve-image-repos --resolve-s3 --config-env $DAITA_STAGE \
        --stack-name "$DAITA_STAGE-${INFRA_APPLICATION}-app" \
        --s3-prefix "$DAITA_STAGE-${INFRA_APPLICATION}-app" \
        --region $AWS_REGION \
        --parameter-overrides $parameters_override | tee -a output.txt


shopt -s extglob

declare -A dict_output
filename="output.txt"

is_first_line_value=false
first_line=""
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


PublicSubnetOne=${dict_output["PublicSubnetOne"]}
PublicSubnetTwo=${dict_output["PublicSubnetTwo"]}
ContainerSecurityGroup=${dict_output["ContainerSecurityGroup"]}
VPC=${dict_output["VPC"]}
VPCEndpointSQSDnsEntries=${dict_output["VPCEndpointSQSDnsEntries"]}
VpcEndointSQS=${dict_output["VpcEndointSQS"]}
VPCEndpointS3=${dict_output["VPCEndpointS3"]}

EFSFileSystemId=${dict_output["EFSFileSystemId"]}
EFSAccessPoint=${dict_output["EFSAccessPoint"]}
EFSAccessPointArn=${dict_output["EFSAccessPointArn"]}

###======= Store output to file ==========
echo "PublicSubnetOne=$PublicSubnetOne" > $OUTPUT_BUILD_DAITA
echo "PublicSubnetTwo=$PublicSubnetTwo" >> $OUTPUT_BUILD_DAITA
echo "ContainerSecurityGroup=$ContainerSecurityGroup" >> $OUTPUT_BUILD_DAITA
echo "VPC=$VPC" >> $OUTPUT_BUILD_DAITA
echo "VPCEndpointSQSDnsEntries=$VPCEndpointSQSDnsEntries" >> $OUTPUT_BUILD_DAITA

echo "EFSFileSystemId=$EFSFileSystemId" >> $OUTPUT_BUILD_DAITA
echo "EFSAccessPoint=$EFSAccessPoint" >> $OUTPUT_BUILD_DAITA
echo "EFSAccessPointArn=$EFSAccessPointArn" >> $OUTPUT_BUILD_DAITA

