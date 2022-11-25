#! /bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo $SCRIPT_DIR

###===== read from config file
echo ==1==. Read the configure file
if [[ $1 == "dev" ]]
then
    configfile=$SCRIPT_DIR/main_config_dev.cnf
else
    if [[ $1 == "prod" ]]
    then
        configfile=$SCRIPT_DIR/main_config_prod.cnf
    else
    echo "Please choose the env is dev/prod"
        exit
    fi
fi

echo $configfile


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

### output data path
output_data=$SCRIPT_DIR/$OUTPUT_BUILD_DAITA_NAME
output_fe_config=$SCRIPT_DIR/$OUTPUT_FOR_FE


### save FE config
echo "### config for daita_env: $DAITA_STAGE   annotation_env: $ANNOTATION_STAGE  ###" > $output_fe_config
echo "REACT_APP_ENV=development" >> $output_fe_config


### build infrastructure that use for another application
echo ==============Building:  INFRA ==========================
bash ./infrastructure-def-app/build_infra_app.sh "$configfile" "$output_data" "$output_fe_config"

### build daita app and annotation ap
if [[ $IS_BUILD_DAITA == "y" ]] || [[ $IS_BUILD_DAITA == "Y" ]]
then
    echo ==============Building:  DAITA ==========================
    bash ./daita-app/build_daita.sh "$configfile" "$output_data" "$output_fe_config"
fi


if [[ $IS_BUILD_ANNOTATION == "y" ]] || [[ $IS_BUILD_ANNOTATION == "Y" ]]
then
    echo ==============Building:  ANNOTATION ==========================
    bash ./annotation-app/build_annotation.sh "$configfile" "$output_data" "$output_fe_config"
fi