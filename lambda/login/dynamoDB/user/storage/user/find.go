package userstorage

import (
	"daita_module_login/component/common"
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"os"
)

func FindUserID(id, username string) (bool, error) {

	sessionDynamo := driver.CreateDynamoSession()
	input := &dynamodb.GetItemInput{
		TableName: aws.String(usermodel.TBL_USER),
		Key: map[string]*dynamodb.AttributeValue{
			"ID": {
				S: aws.String(id),
			},
			"username": {
				S: aws.String(username),
			},
		},
	}
	req, out := sessionDynamo.GetItemRequest(input)
	err := req.Send()
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("GetItemRequest : %s", err.Error()))
		return false, err
	}
	if len(out.Item) == 0 {
		return false, common.ErrValueNotExist
	}
	data := usermodel.User{
		ID:     *out.Item["ID"].S,
		Status: *out.Item["status"].S,
	}
	if data.Status == "activate" {
		return true, nil
	}
	return false, nil
}
