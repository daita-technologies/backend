package auth

import (
	"daita_module_login/component/common"
	"daita_module_login/component/hash"
	"daita_module_login/component/tokenprovider"
	eventstorage "daita_module_login/dynamoDB/user/storage/event"
	"fmt"
	"net/http"

	"github.com/aws/aws-lambda-go/events"
)

func (app Application) signOuthandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	message := ""
	statusCode := http.StatusOK
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
	if !isCheck {
		message = common.MessageAuthenFailed
		statusCode = http.StatusOK
		return message, statusCode, headers, data, common.ErrAuthenFailed

	}
	if err := eventstorage.FindEventId(info.EventId); err != nil && info.EventId != "" {
		statusCode = http.StatusOK
		message = common.MessageAuthenFailed
		return message, statusCode, headers, data, common.ErrAuthenFailed
	}
	if err := eventstorage.DeleteEventID(info.EventId); err != nil && info.EventId != "" {
		statusCode = http.StatusOK
		message = common.MessageAuthenFailed
		return message, statusCode, headers, data, common.ErrAuthenFailed
	}
	message = fmt.Sprintf("Sign out successful")
	statusCode = http.StatusOK
	return message, statusCode, headers, data, nil
}
func (app Application) ImpSignOut(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.signOuthandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
