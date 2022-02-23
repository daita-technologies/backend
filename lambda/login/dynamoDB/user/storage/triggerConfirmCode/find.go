package triggerConfirmCodeStorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"errors"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"github.com/aws/aws-sdk-go/service/dynamodb/expression"
	"os"
)

func FindUserSendCode(code, user string) (bool, error) {

	sessionDynamo := driver.CreateDynamoSession()
	filt := expression.And(
		expression.Name("code").Equal(expression.Value(code)),
		expression.Name("user").Equal(expression.Value(user)),
	)
	expr, err := expression.NewBuilder().WithFilter(filt).Build()
	params := &dynamodb.ScanInput{
		TableName:                 aws.String(usermodel.TBL_TRIGGER_SEND_CODE),
		ExpressionAttributeNames:  expr.Names(),
		ExpressionAttributeValues: expr.Values(),
		FilterExpression:          expr.Filter(),
	}

	resq, err := sessionDynamo.Scan(params)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error user  %s", err.Error()))
		return false, errors.New("Error get user send code id")
	}

	fmt.Fprintf(os.Stderr, fmt.Sprintf("find  user send code %v successfully", len(resq.Items)))
	if len(resq.Items) == 0 {
		return false, errors.New("Can not find user send code")
	}

	return true, nil
}
