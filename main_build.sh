#! /bin/bash

###===== read from config file
echo ==1==. Read the configure file
configfile=./main_config.cnf

keys=( $(grep -oP '\w+(?==)' "$configfile") )
. "$configfile"

for var in "${keys[@]}"; do
    printf "%s\t=> %s\n" "$var" "${!var}"
done

### confirm the config again
read -p "Are you sure that you want to continue with this configuration [y/N]: " confirm
    confirm=${confirm:-n}

if [[ $confirm == "n" ]] || [[ $confirm == "N" ]]
then
    exit
fi


### build daita app

if [[ $IS_BUILD_DAITA == "yes" ]] || [[ $IS_BUILD_DAITA == "YES" ]]
then
    echo ==============Building:  DAITA ==========================
    bash ./daita-app/build_daita.sh $AWS_REGION $AWS_ACCOUNT_ID $DAITA_STAGE $OUTPUT_BUILD_DAITA
fi


if [[ $IS_BUILD_ANNOTATION == "yes" ]] || [[ $IS_BUILD_ANNOTATION == "YES" ]]
then
    echo ==============Building:  ANNOTATION ==========================
    bash ./annotation-app/build_annotation.sh $AWS_REGION $AWS_ACCOUNT_ID $ANNOTATION_STAGE $OUTPUT_BUILD_DAITA
fi