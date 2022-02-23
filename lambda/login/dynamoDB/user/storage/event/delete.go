package eventstorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"errors"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
)

func DeleteEventID(event_id string) error {

	sessionDynamo := driver.CreateDynamoSession()
	input := &dynamodb.DeleteItemInput{
		TableName: aws.String(usermodel.TBL_EventID),
		Key: map[string]*dynamodb.AttributeValue{
			"event_ID": {S: aws.String(event_id)},
			"type":     {S: aws.String("AUTH")},
		},
	}

	_, err := sessionDynamo.DeleteItem(input)
	if err != nil {
		return errors.New("Can not delete user id")
	}
	return nil
}
