# Deployment

1. Create new keypair (optional)
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html

2. Create ECS Cluster name
    - Update Cluster name in template parameter
    - Update Cluster name in `config-ecs-cluster.sh` and create base64 string, then update AWS::EC2::LaunchTemplate User data
    ```sh
    base64 config-ecs-cluster.sh
    ```

**Note**
Output file not found while log is successful: root cause due to output folder permisison, because ECS not run task with EC2 root permisison