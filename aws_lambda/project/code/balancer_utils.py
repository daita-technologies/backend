import os

from boto3.dynamodb.conditions import Key, Attr
from utils import convert_current_date_to_iso8601

def get_ec2_id_link_user(table, identity_id):
    """ check already had the ec2 that linked with indentity_id.
    If exist, return the first ec2_id else return None
    """
    
    # get all ec2_id link with assi_id
    response = table.query(
                IndexName = os.environ['IN_INSTANCES'],
                KeyConditionExpression = Key('assi_id').eq(identity_id),
            )
    print('get_ec2_id_link_user: ',response)
    if response.get('Items'):
        if len(response['Items'])>0:
            return response['Items'][0]['ec2_id']
        else:
            return None
    
    return None
    
def get_ec2_id_default(table):
    """ get default ec2
    """
    
    # get all ec2_id link with assi_id
    response = table.query(
                IndexName = os.environ['IN_INSTANCES'],
                KeyConditionExpression = Key('assi_id').eq("default"),
            )
    print('get_ec2_id_link_user: ',response)
    if response.get('Items'):
        if len(response['Items'])>0:
            return response['Items'][0]['ec2_id']
        else:
            return None
    
    return None
    
def get_ec2_available(table):
    """ get available ec2_id in free, if not, assign to default ec2
    """
    
    # get free list ec2
    response = table.query(
                IndexName = os.environ['IN_INSTANCES'],
                KeyConditionExpression = Key('assi_id').eq('free'),
                FilterExpression = Attr('available').eq(True)
            )
    print('get_ec2_available: ',response)
    if response.get('Items') and len(response['Items'])>0:
        return response['Items'][0]
    else:
        # get default ec2
        response = table.query(
                IndexName = os.environ['IN_INSTANCES'],
                KeyConditionExpression = Key('assi_id').eq('default'),
            )
        if response.get('Items') and len(response['Items'])>0:
            return response['Items'][0]
        else:
            return None
            
    return None
    
def db_write_assign_id(table, identity_id, ec2_avai):
    """
    DB write info to DB and update free ec2
    """
    
    # update availabel status of item to False
    response = table.update_item(
            Key={
                'ec2_id': ec2_avai["ec2_id"],
                'assi_id': ec2_avai["assi_id"],
            },
            ExpressionAttributeValues = {
                ':va':  False,
                ':ti': convert_current_date_to_iso8601()
            },
            UpdateExpression = 'SET available = :va, time_update = :ti' 
        )
        
    # add an item to link ec2 with identity_id
    response = table.put_item(
            Item = {
                'ec2_id': ec2_avai["ec2_id"],
                'assi_id': identity_id,
                'time_update': convert_current_date_to_iso8601(),
                'available': False
            } 
        )
    
    return