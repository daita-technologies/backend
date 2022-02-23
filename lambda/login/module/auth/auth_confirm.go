package auth

import (
	"daita_module_login/component/common"
	usermodel "daita_module_login/dynamoDB/user/model"
	triggerConfirmCodeStorage "daita_module_login/dynamoDB/user/storage/triggerConfirmCode"
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func (app Application) authConfirm(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	user := usermodel.UserSignUpConfirm{}
	err := json.Unmarshal([]byte(event.Body), &user)
	message := "Email successfully confirmed"
	statusCode := http.StatusOK
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Unmarshal User %v\n", err))
		message := common.MessageUnmarshalInputJson
		statusCode = http.StatusOK
		return message, statusCode, headers, data, common.ErrUnmarshalInputJson
	}

	//inputConfirmEmail := &cognitoidentityprovider.ConfirmSignUpInput{
	//	ClientId:         aws.String(app.Configure.ClientPooID),
	//	ConfirmationCode: aws.String(user.ConfirmCode),
	//	Username:         aws.String(user.Username),
	//}
	//_, err = app.Coginto.ConfirmSignUp(inputConfirmEmail)
	verify, err := triggerConfirmCodeStorage.FindUserSendCode(user.ConfirmCode, user.Username)
	// check error or check verify success
	if err != nil || !verify {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Email confirmation failed %v\n", err.Error()))
		message = common.MessageConfirmWrongCodeSignUP
		statusCode = http.StatusOK
		return message, statusCode, headers, data, common.ErrWrongConfirmCodeSignUp
	}
	//
	err = triggerConfirmCodeStorage.DeleteUserSendCode(user.ConfirmCode, user.Username)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("triggerConfirmCodeStorage delete user send code: %s", err.Error()))
		message := fmt.Sprintf("Error: %s", err.Error())
		return message, statusCode, headers, data, err

	}
	_, err = app.Coginto.AdminConfirmSignUp(&cognitoidentityprovider.AdminConfirmSignUpInput{
		UserPoolId: aws.String(app.Configure.UserPoolID),
		Username:   aws.String(user.Username),
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("cognito AdminConfirmSignUp error: %s", err.Error()))
		message := fmt.Sprintf("Error: %s", err.Error())
		return message, statusCode, headers, data, err

	}
	params := cognitoidentityprovider.AdminUpdateUserAttributesInput{
		UserAttributes: []*cognitoidentityprovider.AttributeType{
			{
				Name:  aws.String("email_verified"),
				Value: aws.String("true"),
			},
		},
		UserPoolId: aws.String(app.Configure.UserPoolID),
		Username:   aws.String(user.Username),
	}

	_, err = app.Coginto.AdminUpdateUserAttributes(&params)

	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("cognito AdminUpdateUserAttributes error: %s", err.Error()))
		message := fmt.Sprintf("Error: %s", err.Error())
		return message, statusCode, headers, data, err

	}

	return message, statusCode, headers, data, nil
}

func (app Application) ImpAuthConfirm(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.authConfirm(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
