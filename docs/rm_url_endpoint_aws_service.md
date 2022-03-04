- [Project function APIs](#project-function-apis)
  - [Project create](#project-create)
  - [Project create sample](#project-create-sample)
  - [Project Delete Images](#project-delete-images)
  - [Project Delete](#project-delete)
  - [Project list](#project-list)
  - [Project list info](#project-list-info)
  - [Project Info](#project-info)
  - [Project Update Information](#project-update-information)
  - [Project list data in project](#project-list-data-in-project)
  - [Project Download Images](#project-download-images)
    - [Create Download task](#create-download-task)
    - [Update progress of download task](#update-progress-of-download-task)
  - [Project Upload Images](#project-upload-images)
    - [Check exist of filename in S3](#check-exist-of-filename-in-s3)
    - [Update data to server after uploaded to S3 from client](#update-data-to-server-after-uploaded-to-s3-from-client)
- [Generate Images API](#generate-images-api)
  - [List all methods](#list-all-methods)
  - [Generate images](#generate-images)
  - [Get current progress of task](#get-current-progress-of-task)
- [Balancer API](#balancer-api)
  - [register ec2_id for a new user](#register-ec2_id-for-a-new-user)
  - [start ec2 of user](#start-ec2-of-user)
- [Authentication APIs](#authentication-apis)
  - [API Sign up](#api-sign-up)
  - [API Login](#api-login)
  - [API Test](#api-test)
  - [API Log Out](#api-log-out)
  - [API confirm email](#api-confirm-email)
  - [API resend confirm code](#api-resend-confirm-code)
  - [API resend confirm code forgot password](#api-resend-confirm-code-forgot-password)
  - [API forgot password](#api-forgot-password)
  - [API refresh token](#api-refresh-token)
  - [API send mail](#api-send-mail)
  - [API template invite mail](#api-template-invite-mail)
  - [API Login google](#api-login-google)

# Project function APIs
## Project create
URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/create

Create new project for user with id_token from project name

REQUEST BODY:

    - id_token          | string    | require   | id_token return from login function
    - access_token      | string    | require   | access_token return from login function, note that it is different with access_key from credential
    - project_name      | string    | require   | project name, note that this project name must be unique for an user, server will return error if project_name is duplicated
    - project_info      | string    | optional  | description of project

RESPONSE BODY:

    - data
        - project_id        | string    | project_id unquie for an project
        - s3_prefix         | string    |s3 prefix for project, use it for upload and download data
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXCEPTION EXPLAINATION:

    - ConditionalCheckFailedException('An error occurred (ConditionalCheckFailedException) when calling the PutItem operation: The conditional request failed')
        User already created project with project_name before


## Project create sample
URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/create_sample

FUNCTION:

    Create sample project with provided data

REQUEST BODY:

    - id_token          | string    | require   | id_token return from login function
    - access_token      | string    | require   | access_token return from login function, note that it is different with access_key from credential
    - project_info      | string    | optional  | description of project

RESPONSE BODY:

    - data
        - project_id        | string    | project_id unquie for an project
        - s3_prefix         | string    |s3 prefix for project, use it for upload and download data
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXCEPTION EXPLAINATION:

    - ConditionalCheckFailedException('An error occurred (ConditionalCheckFailedException) when calling the PutItem operation: The conditional request failed')
        User already created project with project_name before

EXAMPLE 

    Request:
    {
        "id_token": {{id_token}},
        "access_token": {{access_token}}
    }

    Response 
    {
        "data": {
            "project_id": "prj_sample_06a11b38405b4b5eaa4d8f1678ca4b1e",
            "s3_prefix": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/prj_sample_06a11b38405b4b5eaa4d8f1678ca4b1e"
        },
        "error": false,
        "success": true,
        "message": null
    }


## Project Delete Images

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/delete_images

FUNCTION

    Delete selected images in project.

REQUEST BODY

    - id_token          |string     | require   | id token return from server after login
    - project_id        |string     | require   | project_id unique for each project 
    - ls_object_info    | list                        
                        - filename      |string     |require    | file name of data. This file name will be unique for each project.                        
                        - size          |number     |require    | size of data, must be in the 'byte' unit
                        - type_method   |string     |require    | type mrthod of data, value is in ORIGINAL | PREPROCESS | AUGMENT                        

RESPONSE BODY

    - data                  | {}
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "project_id": {{project_id}},
        "ls_object_info": [
            {
                "filename": "a.png",
                "type_method": "ORIGINAL",
                "size": 4000
            }
        ]
    }

    Response
    {
        "data": {},
        "error": false,
        "success": true,
        "message": null
    }

## Project Delete

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/delete

FUNCTION

    Delete selected project.

REQUEST BODY

    - id_token          |string     | require   | id token return from server after login
    - project_id        |string     | require   | project_id unique for each project 
    - project_name      |string     | require   | project name                      

RESPONSE BODY

    - data                  | {}
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXCEPTION EXPLAINATION:

    - There are {num_tasks} tasks are running. Please stop all tasks before deleting the project!

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "project_name": {{project_name}},
        "project_id": {{project_id}}
    }

    Response
    {
        "data": {},
        "error": false,
        "success": true,
        "message": null
    }

## Project list
URL:  https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/create

FUNCTION:

    List all projects of user

TYPE

    POST

REQUEST BODY:

    - id_token          | string    | id_token return from login function    

RESPONSE BODY:

    - data
        - items             | list
                            - project_name
                                - S             | string    | name of project
                            - project_id
                                - S             | string    | project id
                            - s3_prefix       
                                - S             | string    | link to s3_prefix of project
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXCEPTION EXPLAINATION:


## Project list info
URL:  https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/list_info

FUNCTION:

    List all projects with all info:
        + summary information
        + list running task
        + project info

TYPE

    POST

REQUEST BODY:

    - id_token          | string    | id_token return from login function    

RESPONSE BODY:

    - data                  | list        
                            - project_name      | string    | name of project
                            - project_id        | string    | id of project
                            - s3_prefix         | string    | s3 prefix on s3 of project
                            - ls_task           | list
                                                - task_id       | string    | id of task
                                                - project_id    | string    | id of project
                            - groups            |  if no data in project, it will return {}
                                                - ORIGINAL      | exist if there are any data in the original
                                                            - count     | number    | total images in original of project
                                                            - size      | number    | total size in original of project
                                                - PREPROCESS    | exist if there are any data in the preprocess
                                                            - count     | number    | total images in preprocess of project
                                                            - size      | number    | total size in preprocess of project
                                                - AUGMENT       | exist if there are any data in the augment
                                                            - count     | number    | total images in augment of project
                                                            - size      | number    | total size in augment of project   
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXCEPTION EXPLAINATION:

EXAMPLE 

    Request:
    {
        "id_token": {{id_token}}
    }

    Response 
    {
        "data": [
            {
                "project_name": "project_A",
                "project_id": "project_A_c02ea544e58c4fbf89ef310b13f05621",
                "s3_prefix": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_c02ea544e58c4fbf89ef310b13f05621",
                "ls_task": [
                    {
                        "task_id": "abc123",
                        "project_id": "project_A_c02ea544e58c4fbf89ef310b13f05621"
                    }
                ],
                "groups": {
                    "ORIGINAL": {
                        "count": 0,
                        "size": 1000
                    }
                }
            },
            {
                "project_name": "project_B",
                "project_id": "project_B_43faaebdee7c418491754d7b571008b8",
                "s3_prefix": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_B_43faaebdee7c418491754d7b571008b8",
                "ls_task": [],
                "groups": {}
            }
        ],
        "error": false,
        "success": true,
        "message": null
    }

## Project Info
URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/info

FUNCTION

    Get detail information of a project name, including total data, total size, total original data, total generation data
    In case we have not update any data yet, it will return the project_id info

TYPE

    POST

REQUEST BODY

    - id_token          |string     | id token return from server after login
    - project_name      |string     | project name
                        

RESPONSE BODY

    - data                  |                            
                            - identity_id       | string        | identity id of user
                            - project_name      | string        | project name
                            - project_id        | string        | project id
                            - times_generated   | number        | times gerated images
                            - ls_task           | list<string>  | list of running task_id, return [] if there is no running task of project
                            - groups
                                        - ORIGINAL      | exist if there are any data in the original
                                                    - count         | number        | total images in original of project
                                                    - size          | number        | total size in original of project
                                                    - data_number   | List<number>  | data number split for train/val/test, it will return null if data not split ever
                                        - PREPROCESS    | exist if there are any data in the preprocess
                                                    - count     | number    | total images in preprocess of project
                                                    - size      | number    | total size in preprocess of project
                                                    - data_number   | List<number>  | data number split for train/val/test, it will return null if data not split ever
                                        - AUGMENT       | exist if there are any data in the augment
                                                    - count     | number    | total images in augment of project
                                                    - size      | number    | total size in augment of project  
                                                    - data_number   | List<number>  | data number split for train/val/test, it will return null if data not split ever                
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE 

    Request:
    {
        "id_token": {{id_token}}, 
        "project_name": {{project_name}}
    }

    Response with no data
    {
        "data": {
            "identity_id": "us-east-2:b7a49377-572d-45bd-bc80-6038a5933579",
            "project_name": "project_B",
            "project_id": "project_B_43faaebdee7c418491754d7b571008b8",
            "times_generated": 0,
            "groups": null
        },
        "error": false,
        "success": true,
        "message": null
    }
    
    Response with data
    {
        "data": {
            "identity_id": "us-east-2:b7a49377-572d-45bd-bc80-6038a5933579",
            "project_name": "project_A",
            "project_id": "project_A_c02ea544e58c4fbf89ef310b13f05621",
            "times_generated": 1,
            "ls_task": [
                "13684d9a-27c5-4331-95a0-facec381f096"
            ],
            "groups": {
                "AUGMENT": {
                    "count": 24,
                    "size": 10291486,
                    "data_number": null
                },
                "ORIGINAL": {
                    "count": 1,
                    "size": 4000,
                    "data_number": [
                        1,
                        0,
                        0
                    ]
                }
            }
        },
        "error": false,
        "success": true,
        "message": null
    }

## Project Update Information 
URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/update_info

FUNCTION

    Update current information of project including project_name or description

TYPE

    POST

REQUEST BODY

    - id_token              |string     | require   | id token return from server after login
    - cur_project_name      |string     | require   | current project name
    - new_project_name      |string     | optional  | new project name, if just update the description please input "" or not input this key
    - new_description       |string     | optional  | new description, if just update the project name please input "" or not input this key    
                        

RESPONSE BODY

    - data
        - project_id        | string    | project_id unquie for an project
        - s3_prefix         | string    | s3 prefix for project, use it for upload and download data
        - is_sample         | boolean   | true if this is the sample project and vv
        - gen_status        | string    | GENERATING/FINISH
        - project_name      | string    | new project name if there is any change
        - description       | string    | new description if there is any change, otherwise it will keep as previous one
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE 

    Request:
    {
        "id_token": {{id_token}},
        "cur_project_name": "rrr1",
        "new_project_name": "rrr2",
        "new_description": "3 update info "
    }

    Response with no data
    {
        "data": {
            "project_id": "rrr_552ef54f591d4e78b8951f2592737241",
            "s3_prefix": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/rrr_552ef54f591d4e78b8951f2592737241",
            "is_sample": false,
            "gen_status": "FINISH",
            "project_name": "rrr2",
            "description": "3 update info "
        },
        "error": false,
        "success": true,
        "message": null
    }    
    

## Project list data in project

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/list_data

FUNCTION: 

    List all s3_key of data in project name. The result will be return as paginator

TYPE

    POST

REQUEST BODY

    - id_token          | string    | id_token return from login function
    - project_id        | string    | id of project
    - type_method       | string    | type of method of data that extracting from DB. The value is one of ORIGINAL | PREPROCESS | AUGMENT
    - num_limit         | number    | number of limitation returned images, maximum is 500
    - next_token        |  in the first time, pass '', in next time, use the next_token value from response
                        - filename      | string      
                        - project_id    | string    

RESPONSE BODY

    - data
        - items             | list
                            - filename          | string    | name of file                           
                            - s3_key            | string    | link to s3_prefix of project
                            - gen_id            | string    | id of generatign method
                            - classtype         | string    | class type of image when generate image (TRAIN/VAL/TEST)
        - next_token        |  return null if no more data need to query
                            - filename          | string    | name of file
                            - project_id        | string    | id of project
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXCEPTION EXPLAINATION

EXAMPLE

    Request body
    {
        "id_token": {{id_token}},
        "project_id": {{project_id}},
        "type_method": "ORIGINAL",
        "next_token": ""
    }

    Response body
    {
        "data": {
            "items": [
                {
                    "filename": "a.jpg",
                    "classtype": "VAL",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_B_43faaebdee7c418491754d7b571008b8/a.jpg",
                    "gen_id": ""
                },
                {
                    "filename": "b.PNG",
                    "classtype": "TRAIN",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_B_43faaebdee7c418491754d7b571008b8/b.PNG",
                    "gen_id": ""
                },
                {
                    "filename": "c.PNG",
                    "classtype": "TEST",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_B_43faaebdee7c418491754d7b571008b8/c.PNG",
                    "gen_id": ""
                }
            ],
            "next_token": null
        },
        "error": false,
        "success": true,
        "message": null
    }

    Request body
    {
        "id_token": {{id_token}},
        "project_id": {{project_id}},
        "num_limit": 5,
        "next_token": {
                "filename": "e.png",
                "project_id": "project_A_6df7f68836dd4eada6df610ca3a175ea"
            }
    }

    response body
    {
        "data": {
            "items": [
                {
                    "filename": "f.png",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_6df7f68836dd4eada6df610ca3a175ea/c.png"
                },
                {
                    "filename": "g.png",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_6df7f68836dd4eada6df610ca3a175ea/b.png"
                },
                {
                    "filename": "uu.png",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_6df7f68836dd4eada6df610ca3a175ea/a.png"
                },
                {
                    "filename": "wew.png",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_6df7f68836dd4eada6df610ca3a175ea/c.png"
                },
                {
                    "filename": "yyy.png",
                    "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_6df7f68836dd4eada6df610ca3a175ea/b.png"
                }
            ],
            "next_token": null
        },
        "error": false,
        "success": true,
        "message": null
    }

## Project Download Images

### Create Download task
URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/download_create

FUNCTION

    Create an download task

REQUEST BODY

    - id_token          |string         | require   | id token return from server after login
    - down_type         |string         | require   | one of ALL or PREPROCESS or AUGMENT or ORIGINAL  
    - project_name      |string         | require   | name of project
    - project_id        |string         | require   | id of project

RESPONSE BODY

    - data                  | 
                            task_id     | string    | id of task, use this task_id to send request track the progress of task                            
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "down_type": "PREPROCESS",
        "project_name": {{project_name}},
        "project_id": {{project_id}}
    }

    Response with running task
    {
        "data": {
            "task_id": "e3b5393a7b0f4a12b78ccfabf34c0485"
        },
        "error": false,
        "success": true,
        "message": null
    }
### Update progress of download task
URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/download_update

FUNCTION

    Get information of current progress of download task

REQUEST BODY

    - id_token          |string         | require   | id token return from server after login
    - task_id           |string         | require   | id of download task         

RESPONSE BODY

    - data                  | 
                            status      | string    | RUNNING or FINISH
                            s3_key      | string    | s3_key of zip file on S3, return null if task is running
                            presign_url | string    | an http convertable link of object, this link expire after 1 hours, return null if task is running
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "task_id": "13eff60d052f47b09b1e93db78d5a89f"
    }

    Response with running task
    {
        "data": {
            "status": "RUNNING",
            "s3_key": null,
            "presign_url": null
        },
        "error": false,
        "success": true,
        "message": null
    }
    
    Response with finished task
    {
        "data": {
            "status": "FINISH",
            "s3_key": "us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/rrr_2dff745c8b4b44ee8cc68b5444288d13/download/rrr_PREPROCESS.zip",
            "presign_url": "https://client-data-test.s3.amazonaws.com/us-east-2%3Ab7a49377-572d-45bd-bc80-6038a5933579/rrr_2dff745c8b4b44ee8cc68b5444288d13/download/rrr_PREPROCESS.zip?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA2XO6HOQ7HGWXJOOX%2F20220121%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20220121T125839Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=88c321a70cc691270503f623a92374e12799a184e4bdf37bfeef575b8d72dde1"
        },
        "error": false,
        "success": true,
        "message": null
    }
## Project Upload Images

### Check exist of filename in S3

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/upload_check

FUNCTION

    Check list data prepare for uploading with current data in DB.

REQUEST BODY

    - id_token          |string     | id token return from server after login
    - project_id        |string     | project_id unique for each project
    - ls_filename       | list
                        <filename>  |string     | filename of data 
                        

RESPONSE BODY

    - data                  | list
                            - filename  
                                - S     | string    | filename that already exist in DB
                            - size
                                - N     | string    | current size of doublicate file
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE 

    Request:
    {
        "id_token": {{id_token}}, 
        "project_id": {{project_id}}, 
        "ls_filename": ["a.png", "h.png"]
    }

    Response
    {
        "data": [
            {
                "filename": {
                    "S": "a.png"
                },
                "size": {
                    "N": "2000"
                }
            }
        ],
        "error": false,
        "success": true,
        "message": null
    }

### Update data to server after uploaded to S3 from client

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/upload_update

FUNCTION

    After uploaded successfully from client to S3, client will send information of these data to server and server will update to DB. In here, we will not auto trigger with put action in client from s3 to lambda.

REQUEST BODY

    - id_token          |string     | require   | id token return from server after login
    - project_id        |string     | require   | project_id unique for each project
    - project_name      |string     | require   | project name
    - type_method       | string    | optional  | type of method that using if it is not original image (is_ori=True), the value should be PREPROCESS or AUGMENT 
    - ls_object_info    | list
                        - s3_key:       |string     |require    | key of data object store in S3, the format must be <bucket>/<identity_id>/<project_id>/<data_name>
                        - filename      |string     |require    | file name of data. This file name will be unique for each project.
                        - hash          |string     |require    | hash string of binary raw data, should use the same hash method.
                        - size          |number     |require    | size of data, must be in the 'byte' unit
                        - is_ori        |boolean    |optional   | if data uploaded by client, it is True, if it was generated from AI so put it false, the default is True
                        - gen_id        |string     |optional   | the id that contain the detail information of generation method. Default is ''
                        - size_old      |number     |optional   | the old size if replace, if image is new, let skip this field

RESPONSE BODY

    - data                  | {}
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}}, 
        "project_id": {{project_id}},
        "project_name": {{project_name}},  
        "ls_object_info": [
            {
                "s3_key": "client-data-test/us-east-2:b7a49377-572d-45bd-bc80-6038a5933579/project_A_6df7f68836dd4eada6df610ca3a175ea/a.png",
                "filename": "a.png",
                "hash": "zzz",
                "size": 3000,
                "size_old": 2000,
                "is_ori": true
            }        
        ]
    }

    Response
    {
        "data": {},
        "error": false,
        "success": true,
        "message": null
    }


# Generate Images API

## List all methods 

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/generate/list_method

FUNCTION

    Get list method for proprocessing and augmenting.

REQUEST BODY

    - id_token          |string     | id token return from server after login

RESPONSE BODY

    - data                  | 
                            augmentation    | list
                                            method_id   | string    | id of method, start with "AUG-xxx"
                                            method_name | string    | name of method
                            preprocessing   | list
                                            method_id   | string    | id of method, start with "PRE-xxx"
                                            method_name | string    | name of method
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}}
    }

    Response
    {
        "data": {
            "augmentation": [
                {
                    "method_id": "AUG-007",
                    "method_name": "random_erase"
                },
                {
                    "method_id": "AUG-013",
                    "method_name": "random_saturation"
                },                
            ],
            "preprocessing": [
                {
                    "method_id": "PRE-001",
                    "method_name": "preprocessing_test_1"
                }
            ]
        },
        "error": false,
        "success": true,
        "message": null
    }


## Generate images

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/generate/images

FUNCTION

    Generate images with preprocessing or augmentation.

REQUEST BODY

    - id_token          |string         | require   | id token return from server after login
    - project_id        |string         | require   | id of project
    - project_name      |string         | require   | project name
    - ls_method_id      | list          | require   | list id of method that will be used to generate images
                        <method_id>     | string
    - data_type         | string        | optional  | type of data that will be used to generate images, the value is one of ORIGINAL | PREPROCESS , default is ORIGINAL
    - num_aug_p_img     | number        | optional  | number of generated images for an input image, max is 5, 
    - data_number       | list<number>  | require   | number of images in train/val/test       

RESPONSE BODY

    - data                  | 
                            task_id         | string    | id of processing task
                            times_generated | number    | times generated images
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "project_id": {{project_id}},
        "project_name": {{project_name}},
        "ls_method_id": ["AUG-001", "AUG-002"],
        "data_type": "ORIGINAL",
        "num_aug_p_img": 1,
        "data_number": [100, 10, 10]
    }

    Response
    {
        "data": {
            "task_id": "",
            "times_generated": 1,
        },
        "error": false,
        "success": true,
        "message": null
    }

## Get current progress of task

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/generate/task_progress

FUNCTION

    Get information of current progress of task

REQUEST BODY

    - id_token          |string         | require   | id token return from server after login
    - task_id           |string         | require   | id of task         

RESPONSE BODY

    - data                  | 
                            task_id     | string    | id of processing task
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "task_id": "1234",
    }

    Response
    {
        "data": {
            
        },
        "error": false,
        "success": true,
        "message": null
    }

# Balancer API

## register ec2_id for a new user

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/balancer/register_ec2

FUNCTION

    Register an free ec2 for a new user, if no free ec2, it will assign to default ec2

REQUEST BODY

    - id_token          |string         | require   | id token return from server after login                  

RESPONSE BODY

    - data                  | None                            
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
    }

    Response
    {
        "data": null,
        "error": false,
        "success": true,
        "message": null
    }

## start ec2 of user

URL: https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/balancer/receiver

FUNCTION

    start an ec2 that assigned to user, ready for augment and preprocess

REQUEST BODY

    - id_token          |string         | require   | id token return from server after login
    - action            |string         | optional  | action with the ec2, value pattern: START | STOP default value is START                

RESPONSE BODY

    - data                  | None                            
    - error                 | boolean   | true if has error, else false
    - success               | boolean   | true if has error, else false
    - message               | string    | None if error is False, else it is the error message

EXAMPLE

    Request
    {
        "id_token": {{id_token}},
        "action": "START"
    }

    Response
    {
        "data": null,
        "error": false,
        "success": true,
        "message": null
    }

# Authentication APIs
## API Sign up
  - POST : 
  
            staging :  https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/user_signup
            dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/user_signup
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

            staging :https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/user_login
            dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/user_login
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
- POST :  

            staging :https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/test
            dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/test
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
- POST :  

        
          staging:https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/user_logout
          dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev
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
- POST :


        staging : https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/auth_confirm
        dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/auth_confirm
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
- POST 

         staging: https://4145bk5g67.execute-api.us-east-2.amazonaws.com/staging/resend_confirmcode
         dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/resend_confirmcode
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
           dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/confirm_code_forgot_password
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
          dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/forgot_password
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
            dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/refresh_token
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
           dev : https://a7la2z0b6i.execute-api.us-east-2.amazonaws.com/dev/template-invite-mail
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