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

func DeleteUserSendCode(code, user string) error {

	sessionDynamo := driver.CreateDynamoSession()
	cond := expression.Name("code").Equal(expression.Value(code))

	// Create a DynamoDB expression from the condition.
	expr, err := expression.NewBuilder().
		WithCondition(cond).
		Build()
	input := &dynamodb.DeleteItemInput{
		TableName: aws.String(usermodel.TBL_TRIGGER_SEND_CODE),
		Key: map[string]*dynamodb.AttributeValue{
			"user": {S: aws.String(user)},
		},
		ExpressionAttributeNames:  expr.Names(),
		ExpressionAttributeValues: expr.Values(),
		ConditionExpression:       expr.Condition(),
	}

	_, err = sessionDynamo.DeleteItem(input)
	if err != nil {
		fmt.Fprintf(os.Stderr, fmt.Sprintf("Delete Item User send code %s", err.Error()))
		return errors.New("Can not delete user ")
	}
	return nil
}
