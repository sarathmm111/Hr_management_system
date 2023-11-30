import argparse
import csv
import configparser
import logging
import os
import sys
import psycopg2 as pg
import requests

logger = None


class HRException(Exception):
    pass


def update_database_name(dbname):
    config = configparser.ConfigParser()
    config.read("config.ini")
    config.set("Database", "dbname", dbname)
    with open("config.ini", "w") as config_file:
        config.write(config_file)


def parse_args():
    config = configparser.ConfigParser()
    config.read("config.ini")

    parser = argparse.ArgumentParser(description="HR management")
    parser.add_argument(
        "-d",
        "--dbname",
        help="Create database table",
        action="store",
        type=str,
        default=config.get("Database", "dbname"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Print detailed logging",
        action="store_true",
        default=False,
    )
    subparser = parser.add_subparsers(dest="subcommand", help="sub-command help")

    parser_initdb = subparser.add_parser(
        "initdb", help="Initialization of tables in the database"
    )

    parser_load = subparser.add_parser(
        "import", help="Load data to database from csvfile"
    )
    parser_load.add_argument("file", help="Providing name of csv file", type=str)

    parser_retrieve = subparser.add_parser(
        "retrieve", help="retrieve data from database"
    )
    parser_retrieve.add_argument(
        "id", help="ID of the employee whose data needs to be generated", type=str
    )
    parser_retrieve.add_argument(
        "--vcard",
        help="Generate vcard details of employee_id to show it on terminal",
        action="store_true",
        default=False,
    )
    parser_retrieve.add_argument(
        "--vcf", help="Generate vcard file", action="store_true", default=False
    )
    parser_retrieve.add_argument(
        "--qrcode", help="Generate qrcode file", action="store_true", default=False
    )

    parser_generate = subparser.add_parser(
        "genvcard", help="Generate vcards for the data"
    )
    parser_generate.add_argument(
        "-n",
        "--number",
        help="Number of records to generate",
        action="store",
        type=int,
        default=10,
    )
    parser_generate.add_argument(
        "--qrcode", help="Generate qrcode file", action="store_true", default=False
    )

    parser_initleave = subparser.add_parser(
        "initleave", help="Input data into leaves table"
    )
    parser_initleave.add_argument(
        "date", help="date of the employee's leave (Date format is : YYYY-MM-DD)"
    )
    parser_initleave.add_argument("employee_id", help="Employee id from details table")
    parser_initleave.add_argument("reason", help="Reason for leave")

    parser_initretrieve_leave = subparser.add_parser(
        "retrieve_leave", help="Obtain data regarding leaves of employee"
    )
    parser_initretrieve_leave.add_argument(
        "employee_id", help="employee id of whom the leave data needs to be retrieved"
    )

    parser_initcsv = subparser.add_parser(
        "retrieve_csv", help="Generate details of employees leaves on csv file"
    )
    parser_initcsv.add_argument(
        "-f",
        "--filename",
        help="Provide file name for generating csv, only file name and no file extention is needed",
        action="store",
        default="leave",
    )

    args = parser.parse_args()
    return args


def logger(is_logger):
    global logger
    if is_logger:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger = logging.getLogger("vcf")
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "[%(levelname)s] %(asctime)s | %(filename)s:%(lineno)d | %(message)s"
        )
    )
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


def create_table(args):
    update_database_name(args.dbname)
    with open("init.sql", "r") as f:
        query = f.read()
        logger.debug(query)
    try:
        conn = pg.connect(dbname=args.dbname)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        logger.info("created tables")
        conn.close()
    except (pg.errors.DuplicateTable, pg.OperationalError) as e:
        raise HRException(e)


def add_data_to_table_details(args):
    conn = pg.connect(dbname=args.dbname)
    cursor = conn.cursor()
    with open(args.file, "r") as f:
        reader = csv.reader(f)
        for last_name, first_name, title, email, ph_no in reader:
            logger.debug("Inserted data of %s", email)
            insert_info = "INSERT INTO details (lastname,firstname,title,email,phone_number) VALUES (%s,%s,%s,%s,%s)"
            cursor.execute(insert_info, (last_name, first_name, title, email, ph_no))
        conn.commit()
    logger.info("data inserted into details table")
    conn.close()


def retrieving_data_from_database(args):
    conn = pg.connect(dbname=args.dbname)
    cursor = conn.cursor()
    try:
        query = "SELECT lastname,firstname,title,email,phone_number FROM details where serial_number = %s"
        cursor.execute(query, (args.id,))
        conn.commit()
        lastname, firstname, title, email, phone_number = cursor.fetchone()
        print(
            f"""Name        : {firstname} {lastname}
              Designation : {title}
              Email       : {email}
              Phone       : {phone_number}"""
        )
        if args.vcard:
            print("\n", implement_vcf(lastname, firstname, title, email, phone_number))
            logger.debug(lastname, firstname, title, email, phone_number)
        if args.vcf:
            if not os.path.exists("vcf_files"):
                os.mkdir("vcf_files")
            imp_vcard = implement_vcf(lastname, firstname, title, email, phone_number)
            with open(f"vcf_files/{email}.vcf", "w") as j:
                j.write(imp_vcard)
                logger.debug(f"generated vcard of{email}")
            logger.info(f"generated vcard of {email}")
        if args.qrcode:
            if not os.path.exists("vcf_files"):
                os.mkdir("vcf_files")
            imp_qrcode = implement_qrcode(
                lastname, firstname, title, email, phone_number
            )
            with open(f"vcf_files/{email}.qr.png", "wb") as f:
                f.write(imp_qrcode)
                logger.debug(f"generated qr code of {email}")
            logger.info(f"Done generating qrcode of {email}")
        conn.close()
    except TypeError as e:
        raise HRException("employee_id not found")


def genrate_vcard_file(args):
    if not os.path.exists("vcf_files"):
        os.mkdir("vcf_files")
    count = 1
    conn = pg.connect(dbname=args.dbname)
    cursor = conn.cursor()
    try:
        query = "SELECT lastname,firstname,title,email,phone_number FROM details"
        cursor.execute(query)
        data = cursor.fetchall()
        details = []
        for i in range(0, args.number):
            details.append(data[i])
            for lastname, firstname, title, email, phone_number in details:
                imp_vcard = implement_vcf(
                    lastname, firstname, title, email, phone_number
                )
                logger.debug("Writing row %d", count)
                count += 1
                with open(f"vcf_files/{email}.vcf", "w") as j:
                    j.write(imp_vcard)
                if args.qrcode:
                    imp_qrcode = implement_qrcode(
                        lastname, firstname, title, email, phone_number
                    )
                    logger.debug(f"Generating qrcode for {email}")
                    with open(f"vcf_files/{email}.qr.png", "wb") as f:
                        f.write(imp_qrcode)
            logger.info(f"generated qrcode of {email}")
        logger.info(f"generated qrcode of {args.number} employees")
        conn.close()
    except IndexError as e:
        raise HRException("number of employee out of limit")


def add_data_to_leaves_table(args):
    conn = pg.connect(dbname=args.dbname)
    cursor = conn.cursor()
    try:
        insert_info = (
            """INSERT INTO leaves (date,employee_id,reason) VALUES (%s,%s,%s)"""
        )
        cursor.execute(insert_info, (args.date, args.employee_id, args.reason))
        conn.commit()
        logger.info("data inserted to leaves table")
        conn.close()
    except (pg.errors.ForeignKeyViolation, pg.errors.UniqueViolation) as e:
        raise HRException(e)


def retrieve_data_from_new_table(args):
    conn = pg.connect(dbname=args.dbname)
    cursor = conn.cursor()
    try:
        retrieve_count = f"""select count (d.serial_number) as count, d.firstname, d.lastname , d.email, g.designation , g.num_of_leaves 
                    from details d join leaves l on d.serial_number = l.employee_id 
                    join designation g on d.title = g.designation 
                    where d.serial_number= %s group by d.serial_number,d.firstname,d.email,g.num_of_leaves,g.designation;"""
        cursor.execute(retrieve_count, (args.employee_id,))
        data = cursor.fetchall()
        if data != []:
            for (
                count_serial_number,
                firstname,
                lastname,
                email,
                designation,
                num_of_leaves,
            ) in data:
                leaves = count_serial_number
                max_leaves = num_of_leaves
                leaves = max_leaves - leaves
                if leaves <= 0:
                    available_leaves = 0
                else:
                    available_leaves = leaves
                d = f"""Name of employee : {firstname} {lastname}
                Email : {email}
                Designation : {designation}
                Maximum alloted leaves : {num_of_leaves}
                Available leaves : {available_leaves}
                Total leaves taken : {count_serial_number}"""
                print(d)
                conn.commit()
        if data == []:
            cursor.execute(
                """select d.num_of_leaves as number,t.firstname,t.lastname , t.email, d.designation from designation d 
                        join details t on d.designation=t.title where t.serial_number = %s;""",
                (args.employee_id,),
            )
            leaves = cursor.fetchall()
            for num_of_leaves, firstname, lastname, email, designation in leaves:
                d = f"""Name of employee : {firstname} {lastname}
                  Email : {email}
                  Designation : {designation}
                  Maximum alloted leaves : {num_of_leaves}
                  Available leaves : {num_of_leaves}
                  Total leaves taken : 0"""
                print(d)
            conn.commit()
        conn.close()
    except UnboundLocalError as e:
        print(f"Error: {e}")
        raise HRException("provided employee id is not in tables")


def generate_leave_csv(args):
    with open(f"{args.filename}.csv", "w") as f:
        data = csv.writer(f)
        a = (
            "Employee_id",
            "firstname",
            "lastname",
            "email",
            "title",
            "Total number of leaves",
            "Leaves left",
        )
        data.writerow(a)

    conn = pg.connect(dbname=args.dbname)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(serial_number) FROM details")
    x = cursor.fetchall()
    for i in x:
        count = i[0]

    for i in range(1, count + 1):
        insert_info = """SELECT l.employee_id FROM leaves l JOIN details d ON l.employee_id = d.serial_number WHERE d.serial_number= %s"""
        cursor.execute(insert_info, (i,))
        data = cursor.fetchall()

        if data == []:
            info = """SELECT d.serial_number, d.firstname, d.lastname, d.email, d.title, g.num_of_leaves
                      FROM details d
                      JOIN designation g ON g.designation = d.title
                      WHERE d.serial_number = %s"""
            cursor.execute(info, (i,))
            n = cursor.fetchall()

            for serial_number, firstname, lastname, email, title, num_of_leaves in n:
                with open(f"{args.filename}.csv", "a") as f:
                    data = csv.writer(f)
                    a = (
                        serial_number,
                        firstname,
                        lastname,
                        email,
                        title,
                        num_of_leaves,
                        num_of_leaves,
                    )
                    data.writerow(a)

        else:
            info = """SELECT d.serial_number, d.firstname, d.lastname, d.email, d.title, g.num_of_leaves
                      FROM details d
                      JOIN designation g ON g.designation = d.title
                      WHERE d.serial_number = %s"""
            cursor.execute(info, (i,))
            n = cursor.fetchall()

            for serial_number, firstname, lastname, email, title, num_of_leaves in n:
                leaves = """SELECT COUNT(l.employee_id), l.employee_id
                            FROM leaves l
                            WHERE l.employee_id = %s
                            GROUP BY l.employee_id"""
                cursor.execute(leaves, (i,))
                m = cursor.fetchall()

                for count_employee_id, employee_id in m:
                    count = count_employee_id

                num_leaves = num_of_leaves
                leaves = num_leaves - count

                if leaves <= 0:
                    leaves_left = 0
                else:
                    leaves_left = leaves

                with open(f"{args.filename}.csv", "a") as f:
                    data = csv.writer(f)
                    a = (
                        serial_number,
                        firstname,
                        lastname,
                        email,
                        title,
                        num_of_leaves,
                        leaves_left,
                    )
                    data.writerow(a)

        conn.commit()

    logger.info(
        f"CSV file {args.filename}.csv consisting of employee's leave data is generated"
    )
    conn.close()


def implement_vcf(last_name, first_name, job, email, ph_no):
    return f"""
BEGIN:VCARD
VERSION:2.1
N:{last_name};{first_name}
FN:{first_name} {last_name}
ORG:Authors, Inc.
TITLE:{job}
TEL;WORK;VOICE:{ph_no}
ADR;WORK:;;100 Flat Grape Dr.;Fresno;CA;95555;United States of America
EMAIL;PREF;INTERNET:{email}
REV:20150922T195243Z
END:VCARD
"""


def implement_qrcode(first_name, last_name, job, email, ph_no):
    reqs = requests.get(
        f"""https://chart.googleapis.com/chart?cht=qr&chs=500x500&chl=BEGIN:VCARD
VERSION:2.1
N:{last_name};{first_name}
FN:{first_name} {last_name}
ORG:Authors, Inc.
TITLE:{job}
TEL;WORK;VOICE:{ph_no}
ADR;WORK:;;100 Flat Grape Dr.;Fresno;CA;95555;United States of America
EMAIL;PREF;INTERNET:{email}
REV:20150922T195243Z
END:VCARD"""
    )
    return reqs.content


def main():
    try:
        args = parse_args()
        logger(args.verbose)
        operations = {
            "initdb": create_table,
            "import": add_data_to_table_details,
            "retrieve": retrieving_data_from_database,
            "genvcard": genrate_vcard_file,
            "initleave": add_data_to_leaves_table,
            "retrieve_leave": retrieve_data_from_new_table,
            "retrieve_csv": generate_leave_csv,
        }
        operations[args.subcommand](args)

    except HRException as e:
        logger.error("Program terminated due to %s", e)
        sys.exit(-1)


if __name__ == "__main__":
    main()
