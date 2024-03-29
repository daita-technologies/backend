import os
config_env = {
    'CLIENTPOOLID': {'dev': '7v8h65t0d3elscfqll090acf9h', 'staging': '4cpbb5etp3q7grnnrhrc7irjoa'},
    'USERPOOLID': {'dev': 'us-east-2_6Sc8AZij7', 'staging': 'us-east-2_ZbwpnYN4g'},
    'IDENTITYPOOLID': {'dev': 'us-east-2:639788f0-a9b0-460d-9f50-23bbe5bc7140', 'staging': 'us-east-2:fa0b76bc-01fa-4bb8-b7cf-a5000954aafb'},
    'LOCATION': {'dev': "https://dev.daita.tech/", 'prod': 'https://app.daita.tech/'},
    'ENDPPOINTREDIRCTLOGINSOCIALOAUTH': {'dev': 'https://izugd01pv1.execute-api.us-east-2.amazonaws.com/dev/auth/login_social', 'staging': 'https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/login_social'},

    'OAUTHENPOINT': {'dev': 'https://authdev.daita.tech/oauth2/token', 'staging': 'https://auth.daita.tech/oauth2/token'},

    'WEBHOOK': {'dev': 'https://hooks.slack.com/services/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', 'staging': 'https://hooks.slack.com/services/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'},
    'CHANNELWEBHOOK': {'dev': '#feedback-daita', 'staging': '#user-feedback'},
    'OAUTH2OFBOT': {'dev': 'xoxb-2966360820768-3760970933602-MoApe9duMpoO5KAa6HaCUzzY'}
}


REGION = "us-east-2"

# TODO: refactor URL to configurable by env var or something
# URL = "https://uflt5029de.execute-api.us-east-2.amazonaws.com/devdaitabeapp/" if os.environ[
#     'MODE'] == 'dev' else "https://119u2071ul.execute-api.us-east-2.amazonaws.com/dev/"
LOCATION = config_env['LOCATION'][os.environ['MODE']]

ENDPOINTCAPTCHAVERIFY = "https://www.google.com/recaptcha/api/siteverify"

# Github OpenID wrapper
# Change these if used with GitHub Enterprise (see below)
GITHUB_API_URL = "https://api.github.com"
GITHUB_LOGIN_URL = "https://github.com"
# config for status of generate task
VALUE_GENERATE_TASK_STATUS_FINISH = "FINISH"
VALUE_GENERATE_TASK_STATUS_ERROR = "ERROR"
VALUE_GENERATE_TASK_STATUS_PENDING = "PENDING"
VALUE_GENERATE_TASK_STATUS_PREPARING_DATA = "PREPARING_DATA"
VALUE_GENERATE_TASK_STATUS_CANCEL = "CANCEL"

# config for process type (task type)
VALUE_PROCESS_TYPE_HEALTHCHECK = "HEALTHCHECK"
VALUE_PROCESS_TYPE_UPLOAD = "UPLOAD"
VALUE_PROCESS_TYPE_DOWNLOAD = "DOWNLOAD"
VALUE_PROCESS_TYPE_PREPROCESS = "PREPROCESS"
VALUE_PROCESS_TYPE_AUGMENT = "AUGMENT"
VALUE_PROCESS_TYPE_REFERENCE_IM = "REFERENCE_IMAGE"
VALUE_LS_PROCESS_TYPE = [VALUE_PROCESS_TYPE_HEALTHCHECK, VALUE_PROCESS_TYPE_DOWNLOAD, VALUE_PROCESS_TYPE_AUGMENT,
                         VALUE_PROCESS_TYPE_PREPROCESS, VALUE_PROCESS_TYPE_REFERENCE_IM,
                         VALUE_PROCESS_TYPE_UPLOAD]

# config for status of healthcheck task
VALUE_HEALTHCHECK_TASK_STATUS_RUNNING = "RUNNING"
VALUE_HEALTHCHECK_TASK_STATUS_FINISH = "FINISH"
VALUE_HEALTHCHECK_TASK_STATUS_ERROR = "ERROR"

### value status create sample project from prebuild dataset
VALUE_STATUS_CREATE_SAMPLE_PRJ_GENERATING = "GENERATING"
VALUE_STATUS_CREATE_SAMPLE_PRJ_FINISH = "FINISH"


VALUE_TASK_RUNNING = "RUNNING"
VALUE_TASK_FINISH = "FINISH"
VALUE_TASK_ERROR = "ERROR"

# config value type method
VALUE_TYPE_METHOD_AUGMENT = "AUGMENT"
VALUE_TYPE_METHOD_PREPROCESS = "PREPROCESS"
VALUE_TYPE_METHOD_NAME_AUGMENT = "AUG"
VALUE_TYPE_METHOD_NAME_PREPROCESS = "PRE"

# config value data type (type of data will be use)
VALUE_TYPE_DATA_ORIGINAL = "ORIGINAL"
VALUE_TYPE_DATA_PREPROCESSED = "PREPROCESS"
VALUE_TYPE_DATA_AUGMENT = "AUGMENT"
LS_ACCEPTABLE_VALUE_GENERATE = [
    VALUE_TYPE_DATA_ORIGINAL, VALUE_TYPE_DATA_PREPROCESSED]

# request + response body + state machine key
KEY_NAME_ID_TOKEN = "id_token"
KEY_NAME_PROJECT_ID = "project_id"
KEY_NAME_PROJECT_NAME = "project_name"
KEY_NAME_LS_METHOD_ID = "ls_method_id"
KEY_NAME_DATA_TYPE = "data_type"
KEY_NAME_NUM_AUG_P_IMG = "num_aug_p_img"
KEY_NAME_DATA_NUMBER = "data_number"
KEY_NAME_S3_PREFIX = "s3_prefix"
KEY_NAME_TIMES_AUGMENT = "times_augment"
KEY_NAME_TIMES_PREPROCESS = "times_preprocess"
KEY_NAME_TASK_ID = "task_id"
KEY_NAME_IDENTITY_ID = "identity_id"
KEY_NAME_TASK_STATUS = "status"
KEY_NAME_FILTER = "filter"                  # for task bashboard API
KEY_NAME_PAGINATION = "pagination"              # for task dashboard API
KEY_SIZE_LS_ITEM_QUERY = "size_list_items_query"   # for task dashboard API
KEY_NAME_PROCESS_TYPE = "process_type"
KEY_NAME_CREATED_TIME = "created_time"
KEY_NAME_REFERENCE_IMAGES = "reference_images"
KEY_NAME_METHOD_ID = "method_id"
KEY_NAME_IS_RESOLUTION = "is_normalize_resolution"
KEY_NAME_AUG_PARAMS = "aug_parameters"

# for save result of reference image to database project table
KEY_NAME_LS_METHOD_CHOOSE = "ls_method_client_choose"

KEY_NAME_RES_AUMENTATION = "augmentation"
KEY_NAME_RES_PREPROCESSING = "preprocessing"

MAX_NUMBER_GEN_PER_IMAGES = 1
MAX_LS_ITEM_QUERY_TASK_DASHBOARD = 100

LS_METHOD_ID_SUPPORT_REFERENCE_IMG = [
    "PRE-002", "PRE-003", "PRE-004", "PRE-005", "PRE-006", "PRE-008"]
LS_METHOD_KEEP_IF_EXIST_PRE001 = ["PRE-001", "PRE-000", "PRE-009"]


### key defined of lambda env
KEY_TABLE_PROJECT = "TABLE_PROJECT"
KEY_TABLE_PROJECT_SUM = "TABLE_PROJECT_SUMMARY"
