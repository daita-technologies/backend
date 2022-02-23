## API Sign UP
  - POST :  https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/user_signup
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
- POST :   https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/user_login
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
      "data": {
        "access_key":String
        "expires_in":String
        "id_token":String
        "identity_id":String
        "secret_key":String
        "session_key":String
        "token":String
        "resfresh_token":String
      },
      "error": Boolean
    }
    ```
   -  Header : x-amzn-remapped-authorization	: "Bearer "The Token""

## API Test
- POST :  https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/test
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
- POST :  https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/user_logout
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
- POST :https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/auth_confirm
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
- POST : https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/resend_confirmcode
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
## API resend confirm code forgot password
- POST : https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/confirm_code_forgot_password
- Request 
  - Content-type	: application/json
  - Body 
    ```
    {
      "username": String
      "password": String
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
## API forgot password
- POST : https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/forgot_password
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
## API refresh token
- POST :   https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/refresh_token
- Request
  - Content-type	: application/json
  - Body 
  ```
  {
    "username": String,
    "refresh_token": String
  }
  ```
- Response 
    - Http code : 200
    ```
    {
      "message": String,
      "data": {
        "access_key":String
        "expires_in":String
        "id_token":String
        "identity_id":String
        "secret_key":String
        "session_key":String
        "token":String
      },
      "error": Boolean
    }
    ```
## API send mail
- POST :   https://54upf5w03c.execute-api.us-east-2.amazonaws.com/staging/send-mail/reference-email
- Request
  - Content-type	: application/json
  - Body 
  ```
    {
      "username":String,
      "destination_email":String
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
## API template invite mail
- GET :  https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/template-invite-mail
- Request :
    - Header : Authorization	: "Bearer "The Token""
- Response :
  - Http code : 200
  ```
    {
      "message": String,
      "data": {
          "template_mail": String
          },
      "error": Boolean
    }
  ```
## API Login google 
- Response 
    - Http code : 200
    ```
    {
      "message": String,
      "data": {
        "access_key":String
        "expires_in":String
        "id_token":String
        "identity_id":String
        "secret_key":String
        "session_key":String
        "token":String
        "resfresh_token":String
      },
      "error": Boolean
    }
    ```
