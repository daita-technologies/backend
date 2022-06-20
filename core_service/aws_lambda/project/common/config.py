import os
config_env ={
    'CLIENTPOOLID': {'dev':'7v8h65t0d3elscfqll090acf9h','staging':'4cpbb5etp3q7grnnrhrc7irjoa'},
    'USERPOOLID':{'dev':'us-east-2_6Sc8AZij7','staging':'us-east-2_ZbwpnYN4g'},
    'IDENTITYPOOLID':{'dev':'us-east-2:639788f0-a9b0-460d-9f50-23bbe5bc7140','staging':'us-east-2:fa0b76bc-01fa-4bb8-b7cf-a5000954aafb'},
    'LOCATION':{'dev':"https://dev.daita.tech/",'staging':'https://app.daita.tech/'},
    'ENDPPOINTREDIRCTLOGINSOCIALOAUTH':{'dev':'https://yf6ayuvru1.execute-api.us-east-2.amazonaws.com/dev/auth/login_social','staging':'https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/login_social'},
    'OAUTHENPOINT':{'dev':'https://daitasociallogin.auth.us-east-2.amazoncognito.com/oauth2/token','staging':'https://auth.daita.tech/oauth2/token'}
}

CLIENTPOOLID = config_env['CLIENTPOOLID'][os.environ['MODE']]
USERPOOLID = config_env['USERPOOLID'][os.environ['MODE']]
REGION = "us-east-2"
IDENTITYPOOLID = config_env['IDENTITYPOOLID'][os.environ['MODE']]
SITEKEYGOOGLE = "6LcqEGMeAAAAAAEDnBue7fwR4pmvNO7JKWkHtAjl"
SECRETKEYGOOGLE = "6LcqEGMeAAAAAOiJAMcg1NNfj6eA62gQPLJAtQMt"
ENDPOINTCAPTCHAVERIFY = "https://www.google.com/recaptcha/api/siteverify"
# Github OpenID wrapper
# Change these if used with GitHub Enterprise (see below)
GITHUB_API_URL = "https://api.github.com"
GITHUB_LOGIN_URL = "https://github.com"
WEBHOOK="https://hooks.slack.com/services/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"
CHANNELWEBHOOK="#user-feedback"
AWS_ACC_ID ='366577564432'
STS_ARN = 'arn:aws:iam::366577564432:role/stscognito'
LOCATION = config_env['LOCATION'][os.environ['MODE']]
ENDPPOINTREDIRCTLOGINSOCIALOAUTH= config_env['ENDPPOINTREDIRCTLOGINSOCIALOAUTH'][os.environ['MODE']]
OAUTHENPOINT = config_env['OAUTHENPOINT'][os.environ['MODE']]