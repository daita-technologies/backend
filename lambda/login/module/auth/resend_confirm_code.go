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
)

func (app Application) reSendConfirmCode(username string) bool {
	//input := &cognitoidentityprovider.ResendConfirmationCodeInput{
	//	Username: aws.String(usename),
	//	ClientId: aws.String(app.Configure.ClientPooID),
	//}
	//_, err := app.Coginto.ResendConfirmationCode(input)
	//if err != nil {
	//	fmt.Fprintf(os.Stderr, fmt.Sprintf("Error resend code : %s", err.Error()))
	//	return false
	//}
	email, err := app.getMailFromUser(username)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error getMailFromUser: %s", err.Error()))
		return false
	}
	codeConfirm := randSeq(6)

	err = triggerConfirmCodeStorage.UpdateUser(usermodel.SendCode{
		User: username,
		Code: codeConfirm,
	})

	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error update triggerConfirmCodeStorage: %s", err.Error()))
		return false
	}

	err = InvokeLambdaStagingSendMail(email, codeConfirm)

	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error invoke lambda staging-sendmail-cognito-service %s", err.Error()))
		return false
	}

	return true
}

func (app Application) reSendEmailConfirmCode(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	user := usermodel.UserResendEmail{}
	err := json.Unmarshal([]byte(event.Body), &user)

	if err != nil {
		message := common.MessageUnmarshalInputJson
		return message, http.StatusOK, headers, data, common.ErrUnmarshalInputJson
	}
	IsSendEmailSuccess := app.reSendConfirmCode(user.UserName)
	if !IsSendEmailSuccess {
		message := common.MessageResendEmailConfirmCodeFailed
		return message, http.StatusOK, headers, data, common.ErrSendEmailFailed
	}
	message := common.MessageResendEmailConfirmCodeSuccessfully
	return message, http.StatusOK, headers, data, nil

}
func (app Application) ImpResendCodeConfirm(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.reSendEmailConfirmCode(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
