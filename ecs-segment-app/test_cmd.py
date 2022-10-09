import boto3

cluster = "segment-ecstask-ServiceApplication-1OPTNXI2VFIW7-ECSCluster-20iFW6ZFwY3Q"
ecsTask = "arn:aws:ecs:us-east-2:737589818430:task-definition/segment-ecstask-ServiceApplication-1OPTNXI2VFIW7-TaskAISegmenationDefinition-4uPNYxdUAF3n:1"
ecs = boto3.client('ecs')
command = ["--input_json_path","data/sample/input.json","--output_folder","data/sample/output"]
response = ecs.run_task(
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

