package userstorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"github.com/aws/aws-sdk-go/service/dynamodb/dynamodbattribute"
	"os"
)

func CreateUser(data usermodel.User) error {
	userMap, err := dynamodbattribute.MarshalMap(data)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("CreateUser : %s", err.Error()))

		return err
	}
	sessionDynamo := driver.CreateDynamoSession()
	input := &dynamodb.PutItemInput{
		Item:      userMap,
		TableName: aws.String(usermodel.TBL_USER),
	}
	_, err = sessionDynamo.PutItem(input)
	if err != nil {
		return err
	}
	return nil
}
