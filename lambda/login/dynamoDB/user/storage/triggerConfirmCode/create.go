package triggerConfirmCodeStorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"github.com/aws/aws-sdk-go/service/dynamodb/dynamodbattribute"
	"os"
)

func CreateSendCode(data usermodel.SendCode) error {
	SendCodeMap, err := dynamodbattribute.MarshalMap(data)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Resend Code : %s", err.Error()))

		return err
	}
	sessionDynamo := driver.CreateDynamoSession()
	input := &dynamodb.PutItemInput{
		Item:      SendCodeMap,
		TableName: aws.String(usermodel.TBL_TRIGGER_SEND_CODE),
	}
	_, err = sessionDynamo.PutItem(input)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Err Create Sendcode  err %s\n:", err.Error()))
		return err
	}
	return nil
}
