import csv
import argparse
import boto3
import logging
from socket import gethostname
from typing import List, Dict
from pathlib import Path
from sys import exit

logging.getLogger("botocore").setLevel(logging.ERROR)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("common")


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate Christmas bonus")
    parser.add_argument(
        "--input_file",
        "-i",
        help="Path to the CSV file containing employee data",
        required=True,
    )
    parser.add_argument(
        "--output_file",
        "-o",
        help="Path to the resulting CSV file with employee data including bonus",
        required=True,
    )
    parser.add_argument(
        "--s3_bucket", "-b", help="Name of the S3 bucket to upload to", required=True
    )
    parser.add_argument(
        "--s3_folder",
        "-f",
        help="Name of the folder in S3 to upload to. Can be multiple folders, like; 'my/folder/name'",
        required=True,
    )

    return parser.parse_args()


def read_data(file_path: str) -> List[Dict]:
    """
    Reads CSV data from `file_path`
    :param file_path: Path on the local file system to a CSV file
    :return:
    """
    logger.info(f"Reading CSV file '{file_path}'")
    try:
        with open(file_path, "r") as input_file:
            reader = csv.DictReader(input_file, delimiter=";")

            return [row for row in reader]

    except FileNotFoundError:
        message = f"The file '{file_path}' was not found."
        logger.error(message)
        exit(message)

    except Exception as exc:
        message = f"There was a problem opening file '{file_path}'. Error: {exc}"
        logger.error(message)
        exit(message)


def upload_to_s3(file_path: str, bucket_name: str, s3_folder_name: str = "") -> bool:
    """
    Uploads the `file_path` to a folder `s3_folder_name` in the S3 bucket `bucket_name`
    :param file_path: Local path to a file to upload
    :param bucket_name: Name of the S3 bucket to upload to
    :param folder_name: Name of the folder in S3 to upload to.
        Can be multiple folders, like; 'my/folder/name'
    :return:
    """
    try:
        s3 = boto3.client("s3", region_name="eu-central-1")
        path_in_s3 = f"{Path(s3_folder_name).joinpath(Path(file_path).name)}"
        logger.info(
            f"Uploading local file '{file_path}' to 's3://{bucket_name}/{path_in_s3}'"
        )
        s3.upload_file(file_path, bucket_name, path_in_s3)

        return True

    except FileNotFoundError:
        message = f"The file '{file_path}' was not found."
        logger.error(message)
        exit(message)

    except Exception as exc:
        message = (
            f"There was a problem uploading file '{file_path}' to S3. Error: {exc}"
        )
        logger.error(message)
        exit(message)


def hostname():
    return f"Running on host '{gethostname()}'"
