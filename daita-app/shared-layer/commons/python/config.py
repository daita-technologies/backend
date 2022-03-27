CLIENT_POOL_ID        = "4cpbb5etp3q7grnnrhrc7irjoa"
USER_POOL_ID          = "us-east-2_ZbwpnYN4g"
REGION              = "us-east-2"
IDENTITY_POOL_ID      = "us-east-2:fa0b76bc-01fa-4bb8-b7cf-a5000954aafb"

### config for status of generate task
VALUE_GENERATE_TASK_STATUS_FINISH           = "FINISH"
VALUE_GENERATE_TASK_STATUS_ERROR            = "ERROR"
VALUE_GENERATE_TASK_STATUS_PENDING          = "PENDING"
VALUE_GENERATE_TASK_STATUS_PREPARING_DATA   = "PREPARING_DATA"

### config value type method
VALUE_TYPE_METHOD_AUGMENT           = "AUGMENT"
VALUE_TYPE_METHOD_PREPROCESS        = "PREPROCESS"
VALUE_TYPE_METHOD_NAME_AUGMENT      = "AUG"
VALUE_TYPE_METHOD_NAME_PREPROCESS   = "PRE"

### config value data type (type of data will be use)
VALUE_TYPE_DATA_ORIGINAL            = "ORIGINAL"
VALUE_TYPE_DATA_PREPROCESSED        = "PREPROCESS"
VALUE_TYPE_DATA_AUGMENT             = "AUGMENT"
LS_ACCEPTABLE_VALUE_GENERATE      = [VALUE_TYPE_DATA_ORIGINAL, VALUE_TYPE_DATA_PREPROCESSED]

### request + response body + state machine key
KEY_NAME_ID_TOKEN           = "id_token" 
KEY_NAME_PROJECT_ID         = "project_id"
KEY_NAME_PROJECT_NAME       = "project_name"
KEY_NAME_LS_METHOD_ID       = "ls_method_id"
KEY_NAME_DATA_TYPE          = "data_type"
KEY_NAME_NUM_AUG_P_IMG      = "num_aug_p_img"
KEY_NAME_DATA_NUMBER        = "data_number"
KEY_NAME_S3_PREFIX          = "s3_prefix"
KEY_NAME_TIMES_AUGMENT      = "times_augment"
KEY_NAME_TIMES_PREPROCESS   = "times_preprocess"
KEY_NAME_TASK_ID            = "task_id"
KEY_NAME_IDENTITY_ID        = "identity_id"

KEY_NAME_RES_AUMENTATION    = "augmentation"
KEY_NAME_RES_PREPROCESSING  = "preprocessing"

MAX_NUMBER_GEN_PER_IMAGES   = 1
 