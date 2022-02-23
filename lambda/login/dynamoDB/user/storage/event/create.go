package eventstorage

import (
	driver "daita_module_login/dynamoDB/user"
	event "daita_module_login/dynamoDB/user/model"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"github.com/aws/aws-sdk-go/service/dynamodb/dynamodbattribute"
	"os"
)

func CreateEventID(event_id event.EventID) error {
	fmt.Fprintf(os.Stderr, fmt.Sprintf("SuccessInsert event_id :  %d\n", event_id.ID))

	eventMap, err := dynamodbattribute.MarshalMap(event_id)
	if err != nil {
		return err
	}
	sessionDynamo := driver.CreateDynamoSession()
	input := &dynamodb.PutItemInput{
		Item:      eventMap,
		TableName: aws.String(event.TBL_EventID),
	}
	_, err = sessionDynamo.PutItem(input)
	if err != nil {
		return err
	}

	return nil
}
