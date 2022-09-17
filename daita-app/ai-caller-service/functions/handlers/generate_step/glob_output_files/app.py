import os
import glob


@error_response
def lambda_handler(event, context):
    result = event
    intput_file = os.path.basename(event.get("intput_file"))
    output_folder = event["request_json"]["output_folder"]
    output_files = glob.glob(os.path.join(output_folder, "*.*"))  # glob every files
    if intput_file:
        output_files = [f for f in output_files if os.path.basename(f) != intput_file]  # exclude input_file
    result["output_images"] = output_files
    return result
