from io import BytesIO
from zipfile import ZipFile
import base64
import os
from botocore.exceptions import ClientError
import time
import glob
from pathlib import Path


def create_zip_object(ls_file):

    # init buffer
    buf = BytesIO()

    # create zip object from ls file
    with ZipFile(buf, "w") as z:
        for file in ls_file:
            file = Path(file)
            if os.path.isdir(file):
                files = glob.glob(os.path.join(file, "**", "*.*"), recursive=True)
                for file_ in files:
                    if os.path.isdir(file_):
                        continue
                    # z.write(file_, os.path.basename(file_))
                    z.write(file_, file_.replace(str(file), ""))
            else:
                z.write(file, os.path.basename(file))

    # open stream for boto3 reading
    buf.seek(0)

    return buf.read()


def exponential_retry(func, error_code, *func_args, **func_kwargs):
    """
    Retries the specified function with a simple exponential backoff algorithm.
    This is necessary when AWS is not yet ready to perform an action because all
    resources have not been fully deployed.

    :param func: The function to retry.
    :param error_code: The error code to retry. Other errors are raised again.
    :param func_args: The positional arguments to pass to the function.
    :param func_kwargs: The keyword arguments to pass to the function.
    :return: The return value of the retried function.
    """
    sleepy_time = 1
    func_return = None
    while sleepy_time < 33 and func_return is None:
        try:
            func_return = func(*func_args, **func_kwargs)

        except ClientError as error:
            if error.response["Error"]["Code"] == error_code:
                print(
                    f"Sleeping for {sleepy_time} to give AWS time to "
                    f"connect resources."
                )
                time.sleep(sleepy_time)
                sleepy_time = sleepy_time * 2
            else:
                raise
    return func_return


def add_lambda_info_to_list(
    ls_lambda_val, lambda_uri, lambda_version, api_resource, api_name
):
    # when lambda_uri return will have the version of lambda function, so, when pass to api, we remove it to run the latest version
    # example:   ...../lambda:1  => ...../lambda
    version_function = lambda_uri.split(":")[-1]
    lambda_uri = lambda_uri[: -(len(version_function) + 1)]
    ls_lambda_val.append((lambda_uri, lambda_version, api_resource, api_name))


# create_zip_object(r'temp\a.zip', [r'backend\lambda\project\code\create_project.py', r'backend\lambda\project\code\utils.py'])
