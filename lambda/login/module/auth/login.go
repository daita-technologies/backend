package auth

import (
	"daita_module_login/component/common"
	"daita_module_login/component/hash"
	"daita_module_login/component/tokenprovider"
	usermodel "daita_module_login/dynamoDB/user/model"
	eventstorage "daita_module_login/dynamoDB/user/storage/event"
	userstorage "daita_module_login/dynamoDB/user/storage/user"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/cognitoidentity"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
	"github.com/aws/aws-sdk-go/service/kms"
)

//
func (app Application) getCredentialsForIdentity(IdToken *string, sess *session.Session) (*cognitoidentity.Credentials, *string, error) {

	svc := cognitoidentity.New(sess)
	idresp, err := svc.GetId(&cognitoidentity.GetIdInput{
		IdentityPoolId: aws.String(common.IDENTITYPOOLID),
		Logins: map[string]*string{
			fmt.Sprintf("cognito-idp.%s.amazonaws.com/%s", common.REGION, common.USERPOOLID): IdToken,
		},
	})
	if err != nil {
		return nil, nil, err
	}
	resq, err := svc.GetCredentialsForIdentity(&cognitoidentity.GetCredentialsForIdentityInput{
		IdentityId: idresp.IdentityId,
		Logins: map[string]*string{
			fmt.Sprintf("cognito-idp.%s.amazonaws.com/%s", common.REGION, common.USERPOOLID): IdToken,
		},
	})
	if err != nil {
		return nil, nil, err
	}
	return resq.Credentials, idresp.IdentityId, nil
}
func CheckExistAliasName(sess *session.Session, aliasName string) (bool, *string, error) {
	svc := kms.New(sess)
	resq, err := svc.ListAliases(nil)
	if err != nil {
		return false, nil, err
	}

	for _, alias := range resq.Aliases {
		res, _ := regexp.MatchString(aliasName, *alias.AliasName)
		if res {
			return true, alias.TargetKeyId, nil
		}
	}
	return false, nil, nil
}

func (app Application) CreateKeyKmsIdentity(identity *string, sess *session.Session) (*string, error) {
	svc := kms.New(sess)
	aliasName := strings.Split(*identity, ":")[1]
	exist, KeyID, err := CheckExistAliasName(sess, aliasName)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error CheckExistAliasName %s\n", err.Error()))
		return nil, err
	}
	if exist {
		return KeyID, nil
	}
	input := &kms.CreateKeyInput{}
	resultCreateKey, err := svc.CreateKey(input)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("resultCrateKey: %s", err.Error()))
		return nil, err
	}
	inputAlias := &kms.CreateAliasInput{
		AliasName:   aws.String("alias/" + aliasName),
		TargetKeyId: resultCreateKey.KeyMetadata.KeyId,
	}
	_, err = svc.CreateAlias(inputAlias)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error create alias: %s", err.Error()))
		return nil, err
	}
	return resultCreateKey.KeyMetadata.KeyId, nil
}

func (app Application) authen(user usermodel.UserLogin, secretHash string) *cognitoidentityprovider.InitiateAuthInput {
	authCognito := &cognitoidentityprovider.InitiateAuthInput{}
	authCognito.ClientId = aws.String(app.Configure.ClientPooID)
	authCognito.AuthFlow = aws.String("USER_PASSWORD_AUTH")
	authCognito.AuthParameters = map[string]*string{
		"USERNAME": aws.String(user.UserName),
		"PASSWORD": aws.String(user.Password),
	}
	return authCognito
}
func (app Application) loginUser(user usermodel.UserLogin, authCognito *cognitoidentityprovider.InitiateAuthInput) (usermodel.UserAuthResponse, error) {
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(common.REGION),
	})
	userAuthResponse := usermodel.UserAuthResponse{}
	res, err := app.Coginto.InitiateAuth(authCognito)

	if err != nil {
		errString := fmt.Sprintf(err.Error())
		for index, pattern := range common.ErrCogintoResponse {
			res, _ := regexp.MatchString(pattern, errString)

			if res {
				fmt.Fprintf(os.Stderr, fmt.Sprintf("Error:  %s", pattern))
				return userAuthResponse, common.ErrorMessageCoginto[index]
			}
		}
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error: authenticated user %s", err))
		return userAuthResponse, err
	}

	token := ""
	IDtoken := ""
	refreshToken := ""
	token_expires := int64(0)
	if res.AuthenticationResult != nil {
		token = *res.AuthenticationResult.AccessToken
		IDtoken = *res.AuthenticationResult.IdToken
		refreshToken = *res.AuthenticationResult.RefreshToken
		token_expires = time.Now().AddDate(0, 0, 1).UnixNano() / int64(time.Millisecond)
	}
	if res.ChallengeName != nil && *res.ChallengeName == "NEW_PASSWORD_REQUIRED" {
		responseChallengeCognito := &cognitoidentityprovider.RespondToAuthChallengeInput{}
		responseChallengeCognito.SetClientId(app.Configure.ClientPooID)
		responseChallengeCognito.SetChallengeName("NEW_PASSWORD_REQUIRED")
		responseChallengeCognito.SetSession(*res.Session)
		responseChallengeCognito.SetChallengeResponses(map[string]*string{
			"USERNAME":     aws.String(user.UserName),
			"NEW_PASSWORD": aws.String(user.Password),
			"SECRET_HASH":  aws.String(hash.CreateSecretHash(app.Configure.ClientPoolSecret, user.UserName, app.Configure.ClientPooID)),
		})

		out, err := app.Coginto.RespondToAuthChallenge(responseChallengeCognito)

		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("error %s", err.Error()))

		}
		token = *out.AuthenticationResult.AccessToken
		IDtoken = *res.AuthenticationResult.IdToken
		refreshToken = *res.AuthenticationResult.RefreshToken
		token_expires = time.Now().AddDate(0, 0, 1).UnixNano() / int64(time.Millisecond)
	}

	if err != nil {
		return usermodel.UserAuthResponse{}, nil
	}

	userAuthResponse.Token = token
	userAuthResponse.IDToken = IDtoken
	userAuthResponse.ResfreshToken = refreshToken

	checkErr, userInfo := tokenprovider.GetToken(token)
	eventId := userInfo.EventId
	credentialUser, identityId, err := app.getCredentialsForIdentity(&IDtoken, sess)
	userAuthResponse.TokenExpiresIn = token_expires
	userAuthResponse.CredentialTokenExpiresIn = ((*credentialUser.Expiration).UnixNano()) / int64(time.Millisecond)
	userAuthResponse.IdentityID = *identityId
	userAuthResponse.SecretKey = *credentialUser.SecretKey
	userAuthResponse.AccessKey = *credentialUser.AccessKeyId
	userAuthResponse.SessionKey = *credentialUser.SessionToken
	if !checkErr {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error dsd"))
	}
	sub, err := tokenprovider.GetInfoFromToken(token, "sub")
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("GetInfoFromToken: %s", err.Error()))
	}
	fmt.Fprintf(os.Stderr, fmt.Sprintf("Sub: %s \n", sub))

	haveOne, err := userstorage.FindUserID(sub, user.UserName)

	if err != nil {
		if err == common.ErrValueNotExist {
			err := userstorage.CreateUser(usermodel.User{
				ID:       sub,
				UserName: user.UserName,
				Role:     "normal",
				Status:   "deactivate",
			})
			if err != nil {
				fmt.Fprintf(os.Stderr, fmt.Sprintf("Error insert database user: %s \n", err.Error()))
			}
		} else {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("Error FindUserID: %s", err.Error()))

		}
	}

	fmt.Fprintf(os.Stderr, fmt.Sprintf("firstLogin: %v", haveOne))
	// first login
	if !haveOne {
		KMSKeyID, err := app.CreateKeyKmsIdentity(&userAuthResponse.IdentityID, sess)
		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("Error KMSKeyID: %s", err.Error()))
		}
		fmt.Fprintf(os.Stderr, fmt.Sprintf("kms %s", *KMSKeyID))

		err = userstorage.UpdateUser(usermodel.User{
			ID:         sub,
			UserName:   user.UserName,
			Status:     "activate",
			IdentityID: userAuthResponse.IdentityID,
			KMSKeyID:   *KMSKeyID,
			UpdateAt:   time.Now().Format(time.RFC3339),
		})
		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("UpdateUser: %s", err.Error()))
		}
	}
	err = eventstorage.CreateEventID(usermodel.EventID{ID: eventId, Type: "AUTH"})
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error insert event_id %s\n", err.Error()))
	} else {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("SuccessInsert event_id: %s\n", eventId))

	}

	return userAuthResponse, nil
}
func (app Application) signInHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {

	data := map[string]interface{}{}
	user := usermodel.UserLogin{}
	err := json.Unmarshal([]byte(event.Body), &user)
	verfiyCatpcha, _ := verifyCaptcha(user.Captcha)
	if !verfiyCatpcha {
		message := common.MessageCaptchaFailed
		return message, http.StatusOK, headers, data, common.ErrCaptchaFailed
	}
	if err != nil {
		message := common.MessageUnmarshalInputJson
		return message, http.StatusOK, headers, data, common.ErrUnmarshalInputJson
	}
	secretHash := hash.CreateSecretHash(app.Configure.ClientPoolSecret, user.UserName, app.Configure.ClientPooID)
	authInput := app.authen(user, secretHash)
	identiFyUser, err := app.loginUser(user, authInput)
	if err != nil {
		message := common.MessageLoginFailed
		if err == common.ErrUserVerifyConfirmCode {
			message := common.MessageUserVerifyConfirmCode
			return message, http.StatusOK, headers, data, common.ErrUserVerifyConfirmCode
		}
		return message, http.StatusOK, headers, data, common.ErrAuthenFailed
	}
	message := common.MessageSignInSuccessfully
	inrec, _ := json.Marshal(identiFyUser)
	json.Unmarshal(inrec, &data)
	return message, http.StatusOK, headers, data, nil
}

func (app Application) ImpLogin(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.signInHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
