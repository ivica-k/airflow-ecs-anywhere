import csv
import logging
from typing import List, Dict

from common import read_data, parse_args, upload_to_s3, hostname

logger = logging.getLogger("christmas_bonus")


def calculate_christmas_bonus(salary: float) -> int:
    """
    Adds 5% bonus to all employees with salary less than or equal to 70000.
    Adds 3% bonus to all employees with salary bigger than 70000
    :param salary: Value of the salary
    :return: Amount of bonus based on the `salary`
    """

    if salary <= 70000.0:
        return int(salary * 0.05)
    else:
        return int(salary * 0.03)


def create_salary_with_bonus(
    employee_data: List[Dict], result_filename: str = "../salary_with_bonus.csv"
) -> str:
    """
    Generates the CSV file with salary bonus column added
    :param employee_data: Data for all employees
    :param result_filename: Path to a CSV file that will have the results
    :return: Path to the generated CSV file
    """
    logger.info(f"Creating the yearly salary with bonus report at '{result_filename}'")
    with open(result_filename, "w") as outfile:
        writer = csv.DictWriter(outfile, delimiter=";", fieldnames=field_names)
        writer.writeheader()

        for emp in employee_data:
            current_salary = float(emp.get("yearly_salary"))
            emp["bonus"] = calculate_christmas_bonus(current_salary)

            writer.writerow(emp)

    return result_filename


if __name__ == "__main__":
    logger.info(hostname())
    field_names = ["id", "first_name", "last_name", "yearly_salary", "bonus"]

    args = parse_args()
    employee_data = read_data(args.input_file)

    local_file = create_salary_with_bonus(employee_data, args.output_file)
    upload_to_s3(local_file, bucket_name=args.s3_bucket, s3_folder_name=args.s3_folder)
