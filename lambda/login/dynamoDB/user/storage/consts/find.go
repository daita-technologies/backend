package constsstorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"errors"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"github.com/aws/aws-sdk-go/service/dynamodb/dynamodbattribute"
	"os"
)

func FindLimitUser(code string) ([]usermodel.Consts, error) {
	sessionDynamo := driver.CreateDynamoSession()

	params := dynamodb.QueryInput{
		TableName:              aws.String(usermodel.TBL_consts),
		KeyConditionExpression: aws.String("#code = :code"),
		ExpressionAttributeNames: map[string]*string{
			"#code": aws.String("code"),
		},
		ExpressionAttributeValues: map[string]*dynamodb.AttributeValue{
			":code": {
				S: aws.String(code),
			},
		},
	}
	resq, err := sessionDynamo.Query(&params)
	if err != nil {
		return []usermodel.Consts{}, errors.New("Error: cann't get number of user limit")
	}
	items := []usermodel.Consts{}
	err = dynamodbattribute.UnmarshalListOfMaps(resq.Items, &items)
	if err != nil {
		return []usermodel.Consts{}, err
	}
	fmt.Fprintf(os.Stderr, fmt.Sprintf("Item %s", items))
	return items, nil
}
