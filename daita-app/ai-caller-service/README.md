# daita-caller-service-app

## Source code structure
It includes the following files and folders:

- api-defs - Definition of http path route
- functions - Code for the application's Lambda functions
- statemachines - Definition for the state machine.
- tests - Unit tests for the Lambda functions' application code.
- events - Event for testing
- template.yaml - A template that defines the application's AWS resources.
- samconfig.toml - The configure of application when deploying

## Deploy

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker [Optional] - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy, run the following in your shell:

```bash
sam build 
sam deploy --guided
```

Note: Please do not change the config in configuration step when deploying if you do not understand what is the effect of your changes.

