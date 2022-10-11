import boto3

cluster = "dev1-anno-ECS-Segmentation-Cluster"
ecsTask = "arn:aws:ecs:us-east-2:737589818430:task-definition/dev1-anno-app-ECSSegmentationServiceApp-1OF75PXKFBI7A-ECSServiceApplication-Y4FTFIB8BLOJ-TaskAISegmenationDefinition-4zw3aVmMbvLt:1"
client = boto3.client('ecs')
command = ["--input_json_path","data/sample/input.json","--output_folder","data/sample/output"]

response = client.run_task(
    cluster = cluster,
    taskDefinition= ecsTask,
    count=1,
       overrides={
            'containerOverrides': [
                {
                    'name': 'test-ecs-task-ecs-segmentations',
                    'command': command,
                },
            ]
        }
)
# waiter = ecs.get_waiter('tasks_stopped')
print(response['tasks'])