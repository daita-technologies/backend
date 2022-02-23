package auth

import (
	"daita_module_login/component/common"
	"daita_module_login/component/hash"
	"daita_module_login/component/tokenprovider"
	usermodel "daita_module_login/dynamoDB/user/model"
	eventstorage "daita_module_login/dynamoDB/user/storage/event"
	"fmt"
	"net/http"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func (app Application) getToken(user usermodel.UserLogin, authCognito *cognitoidentityprovider.InitiateAuthInput) (*string, error) {
	res, err := app.Coginto.InitiateAuth(authCognito)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("authenticated user %v successfully", err))
		return nil, err
	}
	return res.AuthenticationResult.AccessToken, nil

}

func (app Application) testHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	message := fmt.Sprintf("Authentication failed")
	statusCode := http.StatusBadRequest
	if _, ok := event.Headers["Authorization"]; !ok {
		message = common.MessageMissingAuthorizationHeader
		statusCode = http.StatusUnauthorized
		return message, statusCode, headers, data, common.ErrUnmarshalInputJson
	}
	accessToken, err := hash.ExtractTokenFromHeader(event.Headers["Authorization"])
	if err != nil {
		message = common.MessageAuthenFailed
		statusCode = http.StatusOK
		return message, statusCode, headers, data, common.ErrAuthenFailed
	}
	isCheck, info := tokenprovider.GetToken(accessToken)
	eventId := info.EventId

	if isCheck {
		message = fmt.Sprintf("Username %s", info.Username)
		statusCode = http.StatusOK
	}

	if err := eventstorage.FindEventId(eventId); err != nil && eventId != "" {
		message = common.MessageAuthenFailed
		statusCode = http.StatusOK
		return message, statusCode, headers, data, common.ErrAuthenFailed
	}
	return message, statusCode, headers, data, nil
}
func (app Application) ImpTestHandler(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.testHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
