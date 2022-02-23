package auth

import (
	"daita_module_login/component/common"
	"daita_module_login/component/hash"
	usermodel "daita_module_login/dynamoDB/user/model"
	"encoding/json"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
	"net/http"
	"time"
)

func (app Application) authInputRefreshToken(params map[string]*string) *cognitoidentityprovider.InitiateAuthInput {
	authenCognito := &cognitoidentityprovider.InitiateAuthInput{}
	authenCognito.AuthFlow = aws.String("REFRESH_TOKEN_AUTH")
	authenCognito.ClientId = aws.String(app.Configure.ClientPooID)
	authenCognito.AuthParameters = params
	return authenCognito
}

func (app Application) loginRefreshToken(params map[string]*string) (usermodel.UserRefreshTokenResponse, error) {

	authInput := app.authInputRefreshToken(params)
	res, err := app.Coginto.InitiateAuth(authInput)
	if err != nil {

		return usermodel.UserRefreshTokenResponse{}, err
	}
	IDtoken := *res.AuthenticationResult.IdToken
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(common.REGION),
	})
	credentialUser, identityId, err := app.getCredentialsForIdentity(&IDtoken, sess)
	userAuthResponse := usermodel.UserRefreshTokenResponse{
		AccessKey:                *credentialUser.AccessKeyId,
		SecretKey:                *credentialUser.SecretKey,
		SessionKey:               *credentialUser.SessionToken,
		Token:                    *res.AuthenticationResult.AccessToken,
		IdentityID:               *identityId,
		CredentialTokenExpiresIn: ((*credentialUser.Expiration).UnixNano()) / int64(time.Millisecond),
		IDToken:                  IDtoken,
		TokenExpiresIn:           time.Now().AddDate(0, 0, 1).UnixNano() / int64(time.Millisecond),
	}
	return userAuthResponse, nil
}
func (app Application) refreshTokenHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	user := usermodel.UserRefreshToken{}
	err := json.Unmarshal([]byte(event.Body), &user)
	if err != nil {
		message := common.MessageUnmarshalInputJson
		return message, http.StatusOK, headers, data, common.ErrUnmarshalInputJson
	}
	params := map[string]*string{
		"REFRESH_TOKEN": aws.String(user.RefreshToken),
		"SECRET_HASH":   aws.String(hash.CreateSecretHash(app.Configure.ClientPoolSecret, user.UserName, app.Configure.ClientPooID)),
	}
	userResponse, err := app.loginRefreshToken(params)
	if err != nil {
		message := common.MessageRefreshTokenError
		return message, http.StatusOK, headers, data, common.ErrAuthenFailed
	}
	message := common.MessageRefreshTokenSuccessfully
	inrec, _ := json.Marshal(userResponse)
	json.Unmarshal(inrec, &data)
	return message, http.StatusOK, headers, data, nil
}

// implement login refresh token
func (app Application) ImpLoginRefreshToken(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.refreshTokenHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
