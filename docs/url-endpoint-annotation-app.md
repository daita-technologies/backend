

URL_ROOT = [dev]  `https://tq2sk9wusj.execute-api.us-east-2.amazonaws.com/dev`

## Clone project from daita to annotation
- Path: [POST] `/annotation/project/clone_from_daita`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "anno_project_name": "test3_anno",
        "daita_project_name": "test3",
        "project_info": "test annotation"
    }
    ```
- Response
    - Http code: 200

      ```json
      {
          "message": "OK",
          "data": {
              "project_id": "test3_anno_46795ea6be594903b4cf5c621b65405d",
              ### use this value for add new image to s3
              "s3_prefix": "client-annotation-bucket/us-east-2:1fce7cc6-e794-4c1b-801c-77f5cda2f0da/test3_anno_46795ea6be594903b4cf5c621b65405d/raw_data",
              "s3_prj_root": "client-annotation-bucket/us-east-2:1fce7cc6-e794-4c1b-801c-77f5cda2f0da/test3_anno_46795ea6be594903b4cf5c621b65405d",
              "gen_status": "GENERATING",
              "project_name": "test3_anno",
              "link_daita_prj_id": "test3_03e9cf50593e420ab1e035cd7db7f0dd"
          },
          "error": false
      }
      ```

## Get annotation project info
- Path: [POST] `/annotation/project/get_info`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "project_name": "test123_anno"
    }
    ```

- Response
    - Http code: 200

    ```json
      {
          "data": {
              "identity_id": "us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6",
              "project_name": "test123_anno",
              "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b",
              "groups": {
                  "ORIGINAL": {
                      "count": 8,
                      "size": 26746970
                  }
              }
          },
          "error": false,
          "success": true,
          "message": null
      }
    ```

## List all projects of a user
- Path: [POST] `/annotation/project/list_project`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
    }
    ```

- Response
    - Http code: 200

    ```json
    {
        "message": "OK",
        "data": {
            "items": [
                {
                    "gen_status": "FINISH",
                    "project_name": "test123_anno",
                    "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b",
                    "created_date": "2022-09-27T16:44:56.791574"
                }
            ]
        },
        "error": false
    }
    ```

## List all files of a project
- Path: [POST] `/annotation/project/list_project`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b",
        "next_token": "",
        "num_limit": 3
    }
    ```

- Response
    - Http code: 200

    ```json
    {
        "message": "OK",
        "data": {
            "items": [
                {
                    "filename": "20190401145936_camera_sideright_000017967.png",
                    "size": 3096452,
                    "created_time": "2022-09-27T16:45:04.307939",
                    "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20190401145936_camera_sideright_000017967.png"
                },
                {
                    "filename": "20190401145936_camera_sideright_000017963.png",
                    "size": 3090755,
                    "created_time": "2022-09-27T16:45:04.307930",
                    "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20190401145936_camera_sideright_000017963.png"
                },
                {
                    "filename": "20190401145936_camera_sideright_000017937.png",
                    "size": 3025504,
                    "created_time": "2022-09-27T16:45:04.307921",
                    "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20190401145936_camera_sideright_000017937.png"
                }
            ],
            "next_token": {
                "filename": "20190401145936_camera_sideright_000017937.png",
                "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b"
            }
        },
        "error": false
    }
    ```

- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b",
        "next_token": {
                "filename": "20190401145936_camera_sideright_000017937.png",
                "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b"
            },
        "num_limit": 3
    }
    ```

- Response
    - Http code: 200

    ```json
    {
        "message": "OK",
        "data": {
            "items": [
                {
                    "filename": "20190401145936_camera_rearcenter_000017952.png",
                    "size": 3901712,
                    "created_time": "2022-09-27T16:45:04.307912",
                    "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20190401145936_camera_rearcenter_000017952.png"
                },
                {
                    "filename": "20190401145936_camera_frontright_000018002.png",
                    "size": 3006391,
                    "created_time": "2022-09-27T16:45:04.307903",
                    "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20190401145936_camera_frontright_000018002.png"
                },
                {
                    "filename": "20190401121727_camera_frontleft_000013485.png",
                    "size": 3706888,
                    "created_time": "2022-09-27T16:45:04.307894",
                    "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20190401121727_camera_frontleft_000013485.png"
                }
            ],
            "next_token": {
                "filename": "20190401121727_camera_frontleft_000013485.png",
                "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b"
            }
        },
        "error": false
    }
    ```

## Create label category
- Path: [POST] `/annotation/file/create_lable_category`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "file_id": "90830ffc-3255-467f-b9e6-993a2aeeb0d1",
        "category_name": "object segmentation",
        "category_des": "object segmentation description"
    }
    ```

- Response
    - Http code: 200

    ```json
    {
        "message": "OK",
        "data": {
            "category_id": "4d9509ec-42d0-44c7-83eb-472e1d13e1c5",
            "category_name": "object segmentation",
            "category_des": "object segmentation description"
        },
        "error": false
    }
    ```

## Save label
- Path: [POST] `/annotation/file/create_lable_category`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "file_id": "90830ffc-3255-467f-b9e6-993a2aeeb0d1",
        "dict_s3_key": {
            "4d9509ec-42d0-44c7-83eb-472e1d13e1c5": "s3_path_json_label"
        }
    }
    ```

- Response
    - Http code: 200

    ```json
    {
        "message": "OK",
        "data": {},
        "error": false
    }
    ```

## Get file information and the label of file for all category
- Path: [POST] `/annotation/file/get_file_info_n_label`
- Request
  - Body:

    ```json
    {
        "id_token": {{id_token}},
        "project_id": "test123_anno_d92bfec0b0984685961d94a78658344b",
        "filename": "20180810150607_camera_frontleft_000000083.png"
    }
    ```

- Response
    - Http code: 200

    ```json
    {
        "message": "OK",
        "data": {
            "file_info": {
                "filename": "20180810150607_camera_frontleft_000000083.png",
                "size": 3043989,
                "created_time": "2022-09-27T16:45:04.307857",
                "s3_key": "client-annotation-bucket/us-east-2:706ba872-01d3-4e77-b2a1-759d711f97c6/test123_anno_d92bfec0b0984685961d94a78658344b/raw_data/20180810150607_camera_frontleft_000000083.png",
                "file_id": "90830ffc-3255-467f-b9e6-993a2aeeb0d1"
            },
            "label_info": [
                {
                    "s3key_jsonlabel": "s3_path_json_label",
                    "updated_time": "2022-09-27T17:21:31.200059",
                    "category_id": "4d9509ec-42d0-44c7-83eb-472e1d13e1c5",
                    "category_name": "object segmentation",
                    "file_id": "90830ffc-3255-467f-b9e6-993a2aeeb0d1",
                    "category_des": "object segmentation description",
                    "created_time": "2022-09-27T16:52:04.972645"
                }
            ]
        },
        "error": false
    }
    ```