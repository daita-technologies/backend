import os
import json
import glob


EFS_MOUNT_POINT = "/mnt/efs"
CHUNK_SIZE = 100


def lambda_handler(event, context):
    print(event)

    file_url = event["file_url"]
    id_token = body["id_token"]
    project_id = event["project_id"]
    project_name = event["project_name"]
    type_method = event["type_method"]
    filename = event["filename"]
    destination_dir = event["destination_dir"]

    glob_pattern = os.path.join(destination_dir, "*")
    all_files = glob.glob(glob_pattern)
    # get absolute path on EFS
    all_files = list(map(lambda x: os.path.join(destination_dir, x), all_files))
    file_chunks = []
    for size in range(0, len(all_files), CHUNK_SIZE):
        file_chunks.append({"chunk": all_files[size:size + CHUNK_SIZE]})

    print("succeed")

    return {
        "file_url": file_url,
        "project_id": project_id,
        "project_name": project_name,
        "type_method": type_method,
        "filename": filename,
        "destination_dir": destination_dir,
        "file_chunks": file_chunks
    }
