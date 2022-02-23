package auth

import (
	"daita_module_login/component/common"
	"daita_module_login/component/hash"
	"daita_module_login/component/tokenprovider"
	"fmt"
	"net/http"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func (app Application) getMailFromUser(username string) (string, error) {
	input := &cognitoidentityprovider.ListUsersInput{
		UserPoolId: aws.String(app.Configure.UserPoolID),
	}
	email := ""
	res, err := app.Coginto.ListUsers(input)
	if err != nil {
		return email, err
	}
	for _, user := range res.Users {
		fmt.Fprintf(os.Stderr, fmt.Sprintln(*user.Username))
		if *user.Username == username {
			attributes := user.Attributes
			for _, a := range attributes {
				if *a.Name == "email" {
					email = *a.Value
					break
				}
			}
		}
	}
	return email, nil
}

func (app Application) mailTemplateHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	message := ""
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
	if !isCheck {
		message := common.MessageTokenInvalid
		statusCode = http.StatusOK
		return message, statusCode, headers, data, common.ErrTokenInvalid
	}
	email, _ := app.getMailFromUser(info.Username)
	statusCode = http.StatusOK
	data["content"] = fmt.Sprintf("<p>Hi,</p><p>%s has invited you to explore DAITA's recently launched "+
		"<a href=\"https://demo.daita.tech\"style=\"text-decoration:none;color:inherit;border-bottom: solid 2px\">data augmentation platform</a>.</p> "+
		"<p>Building a platform that machine learning engineers and data scientists "+
		"really love is truly hard. But that's our ultimate ambition!</p> <p>Thus, your feedback"+
		" is greatly appreciated, as this first version will still be buggy and missing many features. Please send "+
		"all your thoughts, concerns, feature requests, etc. to contact@daita.tech or simply reply to this e-mail. "+
		"Please be assured that all your feedback will find its way into our product backlog.</p> <p>All our services"+
		" are currently free of charge - so you can go wild! Try it now <a href=\"https://demo.daita.tech\"style=\"text-decoration:none;color:inherit;border-bottom: solid 2px\">here</a>.</p> <p>Cheers,</p> <p>The DAITA Team</p>", email)
	message = common.MessageGetTemapleMailSuccessFully
	return message, statusCode, headers, data, nil

}

func (app Application) ImpEmailTemplate(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.mailTemplateHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
