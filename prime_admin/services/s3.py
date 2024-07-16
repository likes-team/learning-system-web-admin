import logging
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename


def upload_file(file, file_name):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    # Upload the file
    s3_client = boto3.resource("s3")
    bucket_name = "primeklcbucket"
    bucket = s3_client.Bucket(bucket_name)

    try:
        file_path = "cash_flow/{}".format(file_name)
        bucket.Object(file_path).put(Body=file)
        object_url = "https://primeklcbucket.s3.ap-southeast-1.amazonaws.com/{}".format(
            file_path
        )
        return object_url
    except ClientError as e:
        logging.error(e)
        return None
