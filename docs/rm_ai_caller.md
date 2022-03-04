<h1>API Call AI Service</h1>

## API Caller AI
- POST : 3.134.139.184:443/v1/api/request_ai
- Request
  - Content-type	: application/json
  - Body 
  ```
    {
      "identity_id":string,
      "id_token": string
      "images":List Image url of S3,
      "project_id": string,
      "project_name": string,
      "augment_code": List,
      "num_augments_per_image": int
      "project_prefix": string
    }
  ```
- Response
  ```
    {
		"message": "",
		"data": {
			"task_id": string
		},
		"error": Boolean
    }
  ```
## API Check status task AI 
- POST : 3.134.139.184:443/v1/api/check_healthy
- Request
  - Content-type	: application/json
  - Body 
  ```
    {
	    "task_id":string
    }
  ```
- Response
  ```
        {
		"message": "",
		"data": {
			 "status": string
		},
		"error": Boolean
    	}
  ```
  
## Requirements  

```
  	Redis 
  	python 3.8
  ```

  ## Build 
  
 ```
    ./build.sh
 ```

 ## Deploy

 ```
      ./deploy.sh
 ``` 
