## API Sign UP
  - POST :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/user_signup
  - Request
    - Content-type	: application/json
    - Body 
      ```
      {
        "email": String,
        "username": String,
        "password": String
      }
      ```
   - Response
     - Http code : 200

## API Login
- POST :   https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/user_login
- Request
  - Content-type	: application/json
  - Body 
  ```
  {
    "username": String,
    "password": String
  }
  ```
- Response 
    - Http code : 200
    ```
    {
      "message": String,
      "data": {},
      "error": Boolean
    }
    ```
   -  Header : x-amzn-remapped-authorization	: "Bearer "The Token""

## API Test
- POST :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/test
- Request :
    - Header : Authorization	: "Bearer "The Token""
- Response :
  - Http code : 200
  ```
    {
      "message": String,
      "data": {},
      "error": Boolean
    }
  ```
## API Log Out
- POST :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/user_logout
- Request :
  - Header : Authorization	: "Bearer "The Token""
- Response :
```
  {
    "message": String,
    "data": {},
    "error": Boolean
  }
```
## API confirm email 
- POST : https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/auth_confirm
- Request 
  - Content-type	: application/json
  - Body 
    ```
    {
      "username": String,
      "confirm_code": String
    }
    ```
- Response
    - Http code : 200
    ```
    {
      "message":String ,
      "data": {},
      "error": Boolean
    }
    ```
 
## API resend confirm code
- POST : https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/resend_confirmcode
- Request 
  - Content-type	: application/json
  - Body 
    ```
    {
      "username": String
    }
    ```
- Response
    - Http code : 200
    ```
    {
      "message":String ,
      "data": {},
      "error": Boolean
    }
    ```


# Note when moving to new account
1. Update CORS for s3 bucket
2. Create sample folder in S3