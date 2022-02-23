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
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func (app Application) confirmCodeForgotPassword(username, password, confirmCode string) (bool, error) {
	// confirm code
	resq := cognitoidentityprovider.ConfirmForgotPasswordInput{
		Username:         aws.String(username),
		Password:         aws.String(password),
		ConfirmationCode: aws.String(confirmCode),
		ClientId:         aws.String(app.Configure.ClientPooID),
	}
	req, _ := app.Coginto.ConfirmForgotPasswordRequest(&resq)
	err := req.Send()

	//error
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error confirmation code for password recovery: %s", err.Error()))
		return false, err
	}

	return true, nil
}

func (app Application) sendConfirmCodeforgotHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	user := usermodel.UserSendConfirmForgotPassword{}
	err := json.Unmarshal([]byte(event.Body), &user)
	message := ""
	if err != nil {
		message = common.MessageUnmarshalInputJson
		return message, http.StatusOK, headers, data, common.ErrUnmarshalInputJson
	}
	// check password strength
	passwd := user.Password
	secure := true
	tests := []string{".{8,}", "[a-z]", "[A-Z]", "[0-9]", "[^\\d\\w]"}
	for _, test := range tests {
		t, _ := regexp.MatchString(test, passwd)
		if !t {
			secure = false
			break
		}
	}
	if !secure {
		message := common.MessageInvalidPassword
		return message, http.StatusOK, headers, data, common.ErrInvalidPassword
	}
	// check confirm code
	isSuccess, err := app.confirmCodeForgotPassword(user.UserName, user.Password, user.ConfirmCode)
	if err != nil {
		errString := fmt.Sprintf(err.Error())
		for index, pattern := range common.ErrCogintoResponse {
			res, _ := regexp.MatchString(pattern, errString)
			if res {
				message := fmt.Sprintf(common.ErrorMessageCoginto[index].Error())
				return message, http.StatusOK, headers, data, common.ErrorMessageCoginto[index]
			}
		}
		message = common.MessageForgotPasswordConfirmcodeFailed
		return message, http.StatusOK, headers, data, common.ErrSendEmailFailed
	}
	if isSuccess {
		message = common.MessageForgotPasswordConfirmcodeSuccessfully
		return message, http.StatusOK, headers, data, nil
	}
	message = common.MessageForgotPasswordConfirmcodeFailed
	return message, http.StatusOK, headers, data, common.ErrSendEmailFailed
}
func (app Application) ImpConfirmCodeForgotPassword(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {

	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.sendConfirmCodeforgotHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
