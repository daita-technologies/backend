package auth

import (
	"daita_module_login/component/common"
	usermodel "daita_module_login/dynamoDB/user/model"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"regexp"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func (app Application) isEmailedVerify(username *string) (bool, error) {
	//fmt.Sprintf(os.Stderr,fmt.Sprintf(""))
	isVerified := false
	dtl := cognitoidentityprovider.AdminGetUserInput{
		UserPoolId: &app.Configure.UserPoolID,
		Username:   username,
	}
	res, out := app.Coginto.AdminGetUserRequest(&dtl)
	err := res.Send()
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error get user cognito: %s", err.Error()))
		return false, err
	}

	for _, i := range out.UserAttributes {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("%s \n", *i.Name))
		if *i.Name == "email_verified" {
			if *i.Value == "true" {
				isVerified = true
				break
			}
		}
	}
	return isVerified, nil
}

func (app Application) forgotPassword(username *string) (bool, error) {
	checkEmailverify, err := app.isEmailedVerify(username)
	if checkEmailverify {
		inputParam := cognitoidentityprovider.ForgotPasswordInput{
			ClientId: &app.Configure.ClientPooID,
			Username: username,
		}
		proccess, _ := app.Coginto.ForgotPasswordRequest(&inputParam)
		err := proccess.Send()
		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("Error forgot password cognito: %s", err.Error()))
			return false, common.ErrForgotPasswordFailed
		}
		return true, nil

	} else {
		errString := fmt.Sprintf(err.Error())
		for index, pattern := range common.ErrCogintoResponse {
			res, _ := regexp.MatchString(pattern, errString)

			if res {
				fmt.Fprintf(os.Stderr, fmt.Sprintf("Error: %s", pattern))
				return false, common.ErrorMessageCoginto[index]
			}
		}
		return false, nil
	}
	return false, nil
}
func (app Application) forgotHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	user := usermodel.UserForgotPassword{}
	err := json.Unmarshal([]byte(event.Body), &user)
	if err != nil {
		message := common.MessageUnmarshalInputJson
		return message, http.StatusOK, headers, data, common.ErrUnmarshalInputJson
	}
	verfiyCatpcha, _ := verifyCaptcha(user.Captcha)
	if !verfiyCatpcha {
		message := common.MessageCaptchaFailed
		return message, http.StatusOK, headers, data, common.ErrCaptchaFailed
	}
	isSendMailSucceess, err := app.forgotPassword(&user.UserName)
	if isSendMailSucceess {
		return common.MessageForgotPasswordSuccessfully, http.StatusOK, headers, data, nil
	} else if err == common.ErrForgotPasswordUserNotExist {
		message := common.MessageForgotPasswordUsernotExist
		return message, http.StatusOK, headers, data, err
	}
	return common.MessageForgotPasswordFailed, http.StatusOK, headers, data, err

}

func (app Application) ImpForgotPassword(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {

	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.forgotHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
