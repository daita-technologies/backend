package auth

import (
	"daita_module_login/component/common"
	usermodel "daita_module_login/dynamoDB/user/model"
	constsstorage "daita_module_login/dynamoDB/user/storage/consts"
	triggerConfirmCodeStorage "daita_module_login/dynamoDB/user/storage/triggerConfirmCode"
	userstorage "daita_module_login/dynamoDB/user/storage/user"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"regexp"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider"
)

var letters = []rune("0123456789")

func randSeq(n int) string {
	rand.Seed(time.Now().UnixNano())
	b := make([]rune, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}

func (app Application) GetNumberUsersCognito() int {
	input := &cognitoidentityprovider.ListUsersInput{
		UserPoolId: aws.String(app.Configure.UserPoolID),
	}
	res, _ := app.Coginto.ListUsers(input)
	return len(res.Users)
}

func (app Application) CheckInvaildRegister(email string, username string) (bool, bool) {
	input := &cognitoidentityprovider.ListUsersInput{
		UserPoolId: aws.String(app.Configure.UserPoolID),
	}
	res, err := app.Coginto.ListUsers(input)
	if err != nil {
		panic(err)
	}
	isInvalidUser := false
	isInvalidEmail := false
	for _, user := range res.Users {
		fmt.Fprintf(os.Stderr, fmt.Sprintln(*user.Username))
		if *user.Username == username {
			isInvalidUser = true
		}
		attributes := user.Attributes

		for _, a := range attributes {
			if *a.Name == "email" {
				if *a.Value == email {
					isInvalidEmail = true
				}
			}

		}
	}
	return isInvalidEmail, isInvalidUser
}

func (app Application) signUphandler(event events.APIGatewayProxyRequest, headers map[string]string) (string, int, map[string]string, map[string]interface{}, error) {
	data := map[string]interface{}{}
	rand.Seed(time.Now().UnixNano())
	user := usermodel.UserSignUP{}
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

	// Check the number of user is enabled register
	resq, err := constsstorage.FindLimitUser("limit_users")
	current_nums_user := app.GetNumberUsersCognito()
	fmt.Fprintf(os.Stderr, fmt.Sprintf("num user = %s --- resq = %d", current_nums_user, resq[0].Num_value))
	if resq[0].Num_value == current_nums_user {
		message := "We cannot register more users currently. Please contact us at hello@daita.tech. Thank you!"
		return message, http.StatusOK, headers, data, common.ErrCannotRegisterMoreUser
	}

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
	isInvalidEmail, isInvalidUser := app.CheckInvaildRegister(user.Email, user.UserName)
	if isInvalidEmail && isInvalidUser {
		message := common.MessageSignUpInvalid
		return message, http.StatusOK, headers, data, common.ErrUserSignUpInvalid
	} else if isInvalidUser {
		message := common.MessageSignUpUsernameInvalid
		return message, http.StatusOK, headers, data, common.ErrUserSignUpInvalid
	} else if isInvalidEmail {
		message := common.MessageSignUPEmailInvalid
		return message, http.StatusOK, headers, data, common.ErrUserSignUpInvalid
	}
	req, out := app.Coginto.SignUpRequest(&cognitoidentityprovider.SignUpInput{
		ClientId: aws.String(app.Configure.ClientPooID),
		Username: aws.String(user.UserName),
		Password: aws.String(user.Password),
		UserAttributes: []*cognitoidentityprovider.AttributeType{
			{
				Name:  aws.String("email"),
				Value: aws.String(user.Email),
			},
		},
	})
	err = req.Send()
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Sign up %v\n", err))

		message := "Sign up failed"
		errString := fmt.Sprintf(err.Error())
		for index, pattern := range common.ErrCogintoResponse {
			res, _ := regexp.MatchString(pattern, errString)
			if res {
				message := fmt.Sprintf(common.ErrorMessageCoginto[index].Error())
				return message, http.StatusOK, headers, data, common.ErrorMessageCoginto[index]
			}
		}
		return message, http.StatusOK, headers, data, common.ErrSignedUpFailed
	}
	err = userstorage.CreateUser(usermodel.User{
		ID:       *out.UserSub,
		UserName: user.UserName,
		Role:     "normal",
		Status:   "deactivate",
		CreateAt: time.Now().Format(time.RFC3339),
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error insert database user: %s \n", err.Error()))
	}
	codeConfirm := randSeq(6)
	// create code confirm
	err = triggerConfirmCodeStorage.CreateSendCode(usermodel.SendCode{
		User: user.UserName,
		Code: codeConfirm,
	})

	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error insert confirmation code: %s", err.Error()))
		message := fmt.Sprintf("Error insert confirmation code: %s", err.Error())
		return message, http.StatusOK, headers, data, err
	}
	// apply invoke lambda send mail
	err = InvokeLambdaStagingSendMail(user.Email, codeConfirm)
	//sess := session.Must(session.NewSessionWithOptions(session.Options{
	//	SharedConfigState: session.SharedConfigEnable,
	//}))
	//client := lambda.New(sess, &aws.Config{Region: aws.String("us-east-2")})
	////body, err := json.Marshal(map[string]interface{}{
	////	"destination_email": user.Email,
	////	"message_email":     fmt.Sprintf("Demo Your confrim code is %s", codeConfirm),
	////	"subject":           "Confirm Code",
	////})
	//p := Payloadstagingsendmail{
	//	Message_email:     fmt.Sprintf("Demo Your confrim code is %s", codeConfirm),
	//	Destination_email: user.Email,
	//	Subject:           "Confirm Code",
	//}
	//payload, _ := json.Marshal(p)
	//res, err := client.Invoke(&lambda.InvokeInput{FunctionName: aws.String("staging-sendmail-cognito-service"), Payload: payload})
	//
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error invoke lambda staging-sendmail-cognito-service %s", err.Error()))
		message := fmt.Sprintf("Error invoke lambda staging-sendmail-cognito-service %s", err.Error())
		return message, http.StatusOK, headers, data, err
	}
	//} else {
	//	var resp map[string]interface{}
	//
	//	_ = json.Unmarshal(res.Payload, &resp)
	//	fmt.Fprintf(os.Stderr, fmt.Sprintf("Result invoke lambda  staging-sendmail-cognito-service %v", resp))
	//}
	message := fmt.Sprintf("Sign up for user %v was successful", user.UserName)
	return message, http.StatusOK, headers, data, nil
}

func (app Application) ImpSignUp(event events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	headers := map[string]string{"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT",
	}
	message := ""
	statusCode := http.StatusOK
	err := common.ErrInit
	data := map[string]interface{}{}
	message, statusCode, headers, data, err = app.signUphandler(event, headers)
	return common.GenerateResponseBody(message, statusCode, headers, data, err, []string{}), nil
}
