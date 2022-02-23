package eventstorage

import (
	driver "daita_module_login/dynamoDB/user"
	"daita_module_login/dynamoDB/user/model"
	"errors"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"os"
)

func FindEventId(event_id string) error {

	sessionDynamo := driver.CreateDynamoSession()
	params := &dynamodb.QueryInput{
		TableName:              aws.String(usermodel.TBL_EventID),
		KeyConditionExpression: aws.String("#event_id=:EVENT_ID and #TYPE=:TYPE"),
		ExpressionAttributeNames: map[string]*string{
			"#event_id": aws.String("event_ID"),
			"#TYPE":     aws.String("type"),
		},
		ExpressionAttributeValues: map[string]*dynamodb.AttributeValue{
			":EVENT_ID": {
				S: aws.String(event_id),
			},
			":TYPE": {
				S: aws.String("AUTH"),
			},
		},
	}

	resq, err := sessionDynamo.Query(params)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Error eventID %s", err.Error()))
		return errors.New("Error get event id")
	}

	fmt.Fprintf(os.Stderr, fmt.Sprintf("find  eventid %v successfully", len(resq.Items)))
	if len(resq.Items) == 0 {
		return errors.New("Can not find user id")
	}
	return nil
}
