package auth

import (
	"daita_module_login/component/common"
	"daita_module_login/component/tokenprovider"
	usermodel "daita_module_login/dynamoDB/user/model"
	constsstorage "daita_module_login/dynamoDB/user/storage/consts"
	userstorage "daita_module_login/dynamoDB/user/storage/user"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

func (app Application) CheckInvaildRegisterLoginScocial(email string, username string) (bool, bool) {
	input := &cognitoidentityprovider.ListUsersInput{
		UserPoolId: aws.String(app.Configure.UserPoolID),
	}
	res, err := app.Coginto.ListUsers(input)
	if err != nil {
		panic(err)
	}
	isInvalidUser := false
	count_User := 0
	isInvalidEmail := false
	count_Email := 0
	for _, user := range res.Users {
		fmt.Fprintf(os.Stderr, fmt.Sprintln(*user.Username))
		if *user.Username == username {
			count_User += 1
		}
		attributes := user.Attributes

		for _, a := range attributes {
			if *a.Name == "email" {
				if *a.Value == email {
					count_Email += 1
				}
			}

		}
	}
	if count_User > 1 {
		isInvalidUser = true
	}
	if count_Email > 1 {
		isInvalidEmail = true
	}
	return isInvalidEmail, isInvalidUser
}
func (app Application) DeleteUser(username string) error {
	adminDeleteUserInput := &cognitoidentityprovider.AdminDeleteUserInput{
		UserPoolId: aws.String(app.Configure.UserPoolID),
		Username:   aws.String(username),
	}

	_, err := app.Coginto.AdminDeleteUser(adminDeleteUserInput)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error delete user %s", err.Error()))
		return err
	}
	return nil
}

func (app Application) updateVerifyiedEmail(accessToken string) error {
	updateUserAttributesInput := &cognitoidentityprovider.UpdateUserAttributesInput{
		AccessToken: aws.String(accessToken),
		UserAttributes: []*cognitoidentityprovider.AttributeType{
			{
				Name:  aws.String("email_verified"),
				Value: aws.String("true"),
			},
		},
	}

	_, err := app.Coginto.UpdateUserAttributes(updateUserAttributesInput)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error update user %s", err.Error()))
		return err
	}
	return nil
}
func (app Application) Oauth2(code string) (usermodel.UserLoginSocialResponse, error) {
	client := &http.Client{}
	userInfo := usermodel.UserLoginSocialResponse{}
	endpoint := "https://daitasociallogin.auth.us-east-2.amazoncognito.com/oauth2/token"
	params := url.Values{}
	params.Add("code", code)
	params.Add("grant_type", "authorization_code")
	params.Add("redirect_uri", "https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/login_social")
	params.Add("scope", "email+openid+phone+profile")
	params.Add("client_id", app.Configure.ClientPooID)
	req, err := http.NewRequest("POST", endpoint, strings.NewReader(params.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("%s", err.Error()))
		return userInfo, err
	}
	resp, err := client.Do(req)
	respBody, err := ioutil.ReadAll(resp.Body)
	fmt.Fprintf(os.Stderr, fmt.Sprintf("resp body %s", respBody))
	err = json.Unmarshal(respBody, &userInfo)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("%s", err.Error()))
		return userInfo, err
	}
	return userInfo, nil
}

func (app Application) loginSocialHandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	message := ""
	statusCode := http.StatusOK
	value, found := event.QueryStringParameters["code"]
	if found {
		value, err := url.QueryUnescape(value)
		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("%s", err.Error()))
		}
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Value %s", value))
	}
	userOauthInfo, err := app.Oauth2(value)
	sub, _ := tokenprovider.GetInfoFromToken(userOauthInfo.Token, "sub")
	username, _ := tokenprovider.GetInfoFromToken(userOauthInfo.Token, "username")
	//mail, _ := app.getMailFromUser(username)
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(common.REGION),
	})
	resq, err := constsstorage.FindLimitUser("limit_users")
	current_nums_user := app.GetNumberUsersCognito()
	fmt.Fprintf(os.Stderr, fmt.Sprintf("num user = %s --- resq = %d", current_nums_user, resq[0].Num_value))
	if current_nums_user >= resq[0].Num_value {
		message := "We cannot register more users currently. Please contact us at hello@daita.tech. Thank you!"
		errDelete := app.DeleteUser(username)
		if errDelete != nil {
			message := common.MessageErrorDeleteUserSignUp
			return message, http.StatusOK, headers, data, common.ErrMessageErrorDeleteUserSignUp
		}
		return message, http.StatusOK, headers, data, common.ErrCannotRegisterMoreUser
	}

	if err != nil {
		message = common.MessageAuthenFailed
		errDelete := app.DeleteUser(username)
		if errDelete != nil {
			message := common.MessageErrorDeleteUserSignUp
			return message, http.StatusOK, headers, data, common.ErrMessageErrorDeleteUserSignUp
		}
		return message, statusCode, headers, data, err
	}

	//isInvalidEmail, isInvalidUser := app.CheckInvaildRegisterLoginScocial(mail, username)
	//if isInvalidEmail && isInvalidUser {
	//	message := common.MessageSignUpInvalid
	//	errDelete := app.DeleteUser(username)
	//	if errDelete != nil {
	//		message := common.MessageErrorDeleteUserSignUp
	//		return message, http.StatusOK, headers, data, common.ErrMessageErrorDeleteUserSignUp
	//	}
	//	return message, http.StatusOK, headers, data, common.ErrUserSignUpInvalid
	//} else if isInvalidUser {
	//	message := common.MessageSignUpUsernameInvalid
	//	errDelete := app.DeleteUser(username)
	//	if errDelete != nil {
	//		message := common.MessageErrorDeleteUserSignUp
	//		return message, http.StatusOK, headers, data, common.ErrMessageErrorDeleteUserSignUp
	//	}
	//	return message, http.StatusOK, headers, data, common.ErrUserSignUpInvalid
	//} else if isInvalidEmail {
	//	message := common.MessageSignUPEmailInvalid
	//	errDelete := app.DeleteUser(username)
	//	if errDelete != nil {
	//		message := common.MessageErrorDeleteUserSignUp
	//		return message, http.StatusOK, headers, data, common.ErrMessageErrorDeleteUserSignUp
	//	}
	//	return message, http.StatusOK, headers, data, common.ErrUserSignUpInvalid
	//}
	credentialUser, identityId, err := app.getCredentialsForIdentity(&userOauthInfo.ID_Token, sess)
	haveOne, err := userstorage.FindUserID(sub, username)
	if err != nil {
		if err == common.ErrValueNotExist {
			err := userstorage.CreateUser(usermodel.User{
				ID:       sub,
				UserName: username,
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
	userAuthResponse := usermodel.UserAuthResponse{
		Token:                    userOauthInfo.Token,
		IDToken:                  userOauthInfo.ID_Token,
		ResfreshToken:            userOauthInfo.ResfreshToken,
		AccessKey:                *credentialUser.AccessKeyId,
		SecretKey:                *credentialUser.SecretKey,
		SessionKey:               *credentialUser.SessionToken,
		IdentityID:               *identityId,
		TokenExpiresIn:           time.Now().AddDate(0, 0, 1).UnixNano() / int64(time.Millisecond),
		CredentialTokenExpiresIn: ((*credentialUser.Expiration).UnixNano()) / int64(time.Millisecond),
	}
	fmt.Fprintf(os.Stderr, fmt.Sprintf("HaveOne %v", haveOne))
	if !haveOne {
		KMSKeyID, err := app.CreateKeyKmsIdentity(&userAuthResponse.IdentityID, sess)
		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("Error KMSKeyID: %s", err.Error()))
		}
		fmt.Fprintf(os.Stderr, fmt.Sprintf("kms %s", *KMSKeyID))

		err = userstorage.UpdateUser(usermodel.User{
			ID:         sub,
			UserName:   username,
			Status:     "activate",
			IdentityID: userAuthResponse.IdentityID,
			KMSKeyID:   *KMSKeyID,
			UpdateAt:   time.Now().Format(time.RFC3339),
			CreateAt:   time.Now().Format(time.RFC3339),
		})
		if err != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("UpdateUser: %s", err.Error()))
		}
		errSucessfulUpdateVerify := app.updateVerifyiedEmail(userAuthResponse.AccessKey)
		if errSucessfulUpdateVerify != nil {
			fmt.Fprintf(os.Stderr, fmt.Sprintf("Error %s", errSucessfulUpdateVerify))
		}
	}

	inrec, _ := json.Marshal(userAuthResponse)
	json.Unmarshal(inrec, &data)
	return message, statusCode, headers, data, nil
}

func (app Application) ImpSocialLoginHandler(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.loginSocialHandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
