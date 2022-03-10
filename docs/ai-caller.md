# API Call for AI Service

## API Caller: AI Service
- POST: 3.134.139.184:443/v1/api/request_ai
- Request
  - Content-type: application/json
  - Body 
  ```json
  {
      "identity_id": string,
      "id_token": string,
      "images": list image URL of S3,
      "project_id": string,
      "project_name": string,
      "augment_code": list,
      "num_augments_per_image": int,
      "project_prefix": string
  }
  ```
- Response
```json
{
    "message": "",
    "data": {
        "task_id": string
    },
    "error": boolean
}
```

## API Status Checking AI Task 
- POST: 3.134.139.184:443/v1/api/check_healthy
- Request
  - Content-type: application/json
  - Body 
  ```json
  {
      "task_id": string
  }
  ```
- Response
```json
{
    "message": "",
    "data": {
        "status": string
    },
    "error": boolean
}
```

## Requirements  

- Redis 
- Python 3.8

## Build 
  
```bash
./build.sh
```

## Deploy

```bash
./deploy.sh
``` 
