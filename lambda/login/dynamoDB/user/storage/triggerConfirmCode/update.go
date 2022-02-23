package triggerConfirmCodeStorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
)

func UpdateUser(data usermodel.SendCode) error {

	sessionDynamo := driver.CreateDynamoSession()

	param := &dynamodb.UpdateItemInput{
		TableName: aws.String(usermodel.TBL_TRIGGER_SEND_CODE),
		Key: map[string]*dynamodb.AttributeValue{
			"user": {
				S: aws.String(data.User),
			},
		},

		ReturnValues: aws.String("UPDATED_NEW"),
		ExpressionAttributeValues: map[string]*dynamodb.AttributeValue{
			":c": {
				S: aws.String(data.Code),
			},
		},
		ExpressionAttributeNames: map[string]*string{
			"#c": aws.String("code"),
		},
		UpdateExpression: aws.String("set #c = :c"),
	}
	_, err := sessionDynamo.UpdateItem(param)

	if err != nil {
		return err
	}
	return nil
}
