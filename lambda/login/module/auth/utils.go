package auth

import (
	"daita_module_login/component/common"
	usermodel "daita_module_login/dynamoDB/user/model"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/cognitoidentityprovider/cognitoidentityprovideriface"
	"github.com/aws/aws-sdk-go/service/lambda"
)

type Configuration struct {
	ClientPooID      string
	UserPoolID       string
	ClientPoolSecret string
}
type Application struct {
	Configure Configuration
	Coginto   cognitoidentityprovideriface.CognitoIdentityProviderAPI
}
type Payloadstagingsendmail struct {
	// You can also include more objects in the structure like below,
	// but for my purposes body was all that was required
	// Method string `json:"httpMethod"`
	Destination_email string `json:"destination_email"`
	Message_email     string `json:"message_email"`
	Subject           string `json:"subject"`
}

func InvokeLambdaStagingSendMail(email, codeConfirm string) error {
	sess := session.Must(session.NewSessionWithOptions(session.Options{
		SharedConfigState: session.SharedConfigEnable,
	}))
	client := lambda.New(sess, &aws.Config{Region: aws.String("us-east-2")})
	//body, err := json.Marshal(map[string]interface{}{
	//	"destination_email": user.Email,
	//	"message_email":     fmt.Sprintf("Demo Your confrim code is %s", codeConfirm),
	//	"subject":           "Confirm Code",
	//})
	p := Payloadstagingsendmail{
		Message_email:     fmt.Sprintf("<p>Your confirmation code is %s</p>", codeConfirm),
		Destination_email: email,
		Subject:           "Your email confirmation code",
	}
	payload, err := json.Marshal(p)
	res, err := client.Invoke(&lambda.InvokeInput{FunctionName: aws.String("staging-sendmail-cognito-service"), Payload: payload})
	if err != nil {
		//fmt.Fprintf(os.Stderr, fmt.Sprintf("Error invoke lambda  staging-sendmail-cognito-service %s", err.Error()))
		return err
	} else {
		var resp map[string]interface{}

		_ = json.Unmarshal(res.Payload, &resp)
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Result invoke lambda staging-sendmail-cognito-service %v", resp))
	}
	return nil
}

func verifyCaptcha(token string) (bool, error) {
	client := &http.Client{}
	//params := url.Values{}
	endPoint := common.ENDPOINTCAPTCHAVERIFY

	req, err := http.NewRequest("POST", endPoint, nil)
	//req.Hniler.Set("Content-type", "application/x-www-form-urlencoded")

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error Init http request %s", err.Error())
		return false, err
	}
	params := req.URL.Query()
	params.Add("secret", common.SECRETKEYGOOGLE)
	params.Add("sitekey", common.SITEKEYGOOGLE)
	params.Add("response", token)
	req.URL.RawQuery = params.Encode()
	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error http request %s", err.Error())
		return false, err
	}
	respBody, err := ioutil.ReadAll(resp.Body)
	responseVerifyCaptcha := usermodel.ResponseVerfifyCatpcha{}
	err = json.Unmarshal(respBody, &responseVerifyCaptcha)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error ReadAll %s", err.Error())
		return false, err
	}
	fmt.Fprintf(os.Stderr, fmt.Sprintf("resp Body Hostname: %s and Success: %t", responseVerifyCaptcha.Hostname, responseVerifyCaptcha.Success))
	if responseVerifyCaptcha.Success == false {
		return false, nil
	}
	return true, nil
}
