package userstorage

import (
	driver "daita_module_login/dynamoDB/user"
	usermodel "daita_module_login/dynamoDB/user/model"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/dynamodb"
)

func UpdateUser(data usermodel.User) error {

	sessionDynamo := driver.CreateDynamoSession()

	param := &dynamodb.UpdateItemInput{
		TableName: aws.String(usermodel.TBL_USER),
		Key: map[string]*dynamodb.AttributeValue{
			"ID": {
				S: aws.String(data.ID),
			},
			"username": {
				S: aws.String(data.UserName),
			},
		},

		ReturnValues: aws.String("UPDATED_NEW"),
		ExpressionAttributeValues: map[string]*dynamodb.AttributeValue{
			":s": {
				S: aws.String(data.Status),
			},
			":i": {
				S: aws.String(data.IdentityID),
			},
			":k": {
				S: aws.String(data.KMSKeyID),
			},
			":update": {
				S: aws.String(data.UpdateAt),
			},
		},
		ExpressionAttributeNames: map[string]*string{
			"#s":      aws.String("status"),
			"#i":      aws.String("identity_id"),
			"#k":      aws.String("kms_key_id"),
			"#update": aws.String("update_at"),
		},
		UpdateExpression: aws.String("set #s = :s , #i = :i , #k = :k , #update = :update"),
	}
	_, err := sessionDynamo.UpdateItem(param)

	if err != nil {
		return err
	}
	return nil
}
