import csv
import logging
from typing import List, Dict

from common import read_data, parse_args, upload_to_s3, hostname


logger = logging.getLogger("tax_amount")


def calculate_total_tax(
    employee_data: List[Dict], result_filename: str = "../tax_amount.csv"
) -> str:
    """
    Calculates and writes the total tax payable to the government for all employees
    and writes it to a CSV file
    :param employee_data: Data for all employees
    :param result_filename: Path to the generated CSV file
    :return:
    """
    tax_amount = 0
    logger.info(f"Creating the total tax payable report at '{result_filename}'")
    with open(result_filename, "w") as outfile:
        writer = csv.DictWriter(outfile, delimiter=";", fieldnames=field_names)
        writer.writeheader()

        for emp in employee_data:
            current_salary = float(emp.get("yearly_salary"))
            tax_amount += int(current_salary * 0.21)

        writer.writerow({"tax_amount": tax_amount})

    return result_filename


if __name__ == "__main__":
    logger.info(hostname())
    field_names = ["tax_amount"]

    args = parse_args()
    employee_data = read_data(args.input_file)

    local_file = calculate_total_tax(employee_data, args.output_file)
    upload_to_s3(local_file, bucket_name=args.s3_bucket, s3_folder_name=args.s3_folder)
