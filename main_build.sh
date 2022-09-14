#! /bin/bash

###===== read from config file
echo ==1==. Read the configure file
configfile=~/backend/main_config.cnf

keys=( $(grep -oP '\w+(?==)' "$configfile") )
. "$configfile"

### confirm build daita
read -p "Do you want to build DAITA [Y/n]: " IS_BUILD_DAITA
    confirm=${IS_BUILD_DAITA:-y}
read -p "Do you want to build ANNOTATION [Y/n]: " IS_BUILD_ANNOTATION
    confirm=${IS_BUILD_ANNOTATION:-y}

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

if [[ $IS_BUILD_DAITA == "y" ]] || [[ $IS_BUILD_DAITA == "Y" ]]
then
    echo ==============Building:  DAITA ==========================
    bash ./daita-app/build_daita.sh $AWS_REGION $AWS_ACCOUNT_ID $DAITA_STAGE $OUTPUT_BUILD_DAITA
fi


if [[ $IS_BUILD_ANNOTATION == "y" ]] || [[ $IS_BUILD_ANNOTATION == "Y" ]]
then
    echo ==============Building:  ANNOTATION ==========================
    bash ./annotation-app/build_annotation.sh "$configfile"
fi