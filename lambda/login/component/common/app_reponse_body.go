package common

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/events"
	"net/http"
	"os"
)

type ResponseBody struct {
	Message string                 `json:"message"`
	Data    map[string]interface{} `json:"data"`
	Error   bool                   `json:"error"`
}

func GenerateResponseBody(message string, statusCode int, headers map[string]string, data map[string]interface{}, err error, cookie []string) events.APIGatewayProxyResponse {
	headers["access-control-allow-origin"] = "*"
	headers["access-control-allow-headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
	isErr := false
	if err != nil {
		isErr = true
	}
	body, err := json.Marshal(
		ResponseBody{
			Message: message,
			Data:    data,
			Error:   isErr,
		},
	)

	if err != nil {
		fmt.Fprintf(os.Stderr, "unable to marshal reponse %v", err)
		statusCode = http.StatusBadRequest
	}
	var buf bytes.Buffer
	json.HTMLEscape(&buf, body)
	resp := events.APIGatewayProxyResponse{
		StatusCode:      statusCode,
		Headers:         headers,
		Body:            buf.String(),
		IsBase64Encoded: false,
	}
	return resp
}
