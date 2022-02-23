package main

import (
	"daita_module_login/component/common"
	"daita_module_login/module/auth"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func main() {

	cfg := auth.Configuration{
		ClientPooID: common.CLIENTPOOLID,
		UserPoolID:  common.USERPOOLID,
	}
	app := auth.Application{
		Configure: cfg,
		Coginto:   cognitoidentityprovider.New(session.Must(session.NewSession())),
	}
	lambda.Start(app.ImpSocialLoginHandler)
}
