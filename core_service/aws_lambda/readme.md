## API Sign UP
  - POST :
    ```
          staging :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/user_signup
          dev     :  https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/user_signup
    ```
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
- POST :   

  ```
              staging :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/user_login
              dev     :  https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/user_login
  ```
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

## API confirm email 
- POST : 
  ```
              staging :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/auth_confirm
              dev     :  https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/auth_confirm
  ```
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
- POST : 
  ```
              staging :  https://rtv81e9ysk.execute-api.us-east-2.amazonaws.com/staging/resend_confirmcode
              dev     :  https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/resend_confirmcode
  ```
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
- POST : 

 
           staging: https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/confirm_code_forgot_password
           dev : https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/confirm_code_forgot_password
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
- POST :


          staging https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/forgot_password
          dev : https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/forgot_password
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
- POST :    

            staging : https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/refresh_token
            dev :https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/refresh_token
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
- POST :  


         staging: https://54upf5w03c.execute-api.us-east-2.amazonaws.com/staging/send-mail/reference-email
         dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/send-mail/reference-email
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
- GET :   

           staging :https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/template-invite-mail
           dev :https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/template-invite-mail
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


# Note when moving to new account
1. Update CORS for s3 bucket
2. Create sample folder in S3
