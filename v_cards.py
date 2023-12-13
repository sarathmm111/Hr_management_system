import argparse
import csv
import configparser
import logging
import os
import sys
import psycopg2 as pg
import requests
import models
import sqlalchemy as sa
import models
import web

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

    web_parser = subparser.add_parser("web", help="To run program on web")

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
  try:
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)
    engine = models.create_engine(db_uri)
    tables = ['employee','leaves','designation']
    for table in tables:
      table_exists = engine.dialect.has_table(engine.connect(), table , schema='public')

    if table_exists:
       logger.error(f"All tables exists")
    else:
      models.create_all(db_uri)
      designations = [models.Designation(title="Staff Engineer", max_leaves=20),
                      models.Designation(title="Senior Engineer", max_leaves=18),
                      models.Designation(title="Junior Engineer", max_leaves=12),
                      models.Designation(title="Technical Lead", max_leaves=12),
                      models.Designation(title="Project Manager", max_leaves=15)]
      session.add_all(designations)
      session.commit()
      logger.info("Tables created")
  except (sa.exc.OperationalError,pg.OperationalError) as e:
    raise HRException(e)

def add_data_to_table_details(args):
  db_uri = f"postgresql:///{args.dbname}"
  session = models.get_session(db_uri)
  try:
    with open(args.file,'r') as f:
      reader = csv.reader(f)
      for last_name,first_name,title,email,phone in reader:
        q = sa.select(models.Designation).where(models.Designation.title==title)
        designation = session.execute(q).scalar_one()
        employee = models.Employee(lastname=last_name,firstname=first_name,title=designation,email=email,ph_no=phone)
        logger.debug("Inserted data of %s",email)
        session.add(employee)
      session.commit()
    logger.info("data inserted into employee table")
  except (pg.errors.UniqueViolation,sa.exc.IntegrityError) as e:
    raise HRException("data provided already exists in table employee")


def retrieving_data_from_database(args):
  db_uri = f"postgresql:///{args.dbname}"
  session = models.get_session(db_uri)
  try:
    query =  ( sa.select
               (models.Employee.lastname,
                models.Employee.firstname,
                models.Designation.title,
                models.Employee.email,
                models.Employee.ph_no)
               .where(models.Employee.title_id==models.Designation.jobid,
                      models.Employee.empid==args.id)
              )
    x=session.execute(query).fetchall()
    session.commit()
    for lastname,firstname,title,email,phone_number in x:
      print(f"""Name        : {firstname} {lastname}
                Designation : {title}
                Email       : {email}
                Phone       : {phone_number}""")
      if args.vcard:
         print("\n",implement_vcf(lastname,firstname,title,email,phone_number))
         logger.debug(lastname,firstname,title,email,phone_number)
      if args.vcf:
        if not os.path.exists('vcf_files'):
          os.mkdir('vcf_files') 
        imp_vcard = implement_vcf(lastname,firstname,title,email,phone_number)
        with open(f'vcf_files/{email}.vcf','w') as j:
           j.write(imp_vcard)
           logger.debug(f"generated vcard of  {email}")
        logger.info(f"generated vcard of  {email}")
      if args.qrcode:
         if not os.path.exists('vcf_files'):
           os.mkdir('vcf_files')
         imp_qrcode = implement_qrcode(lastname,firstname,title,email,phone_number)
         with open(f'vcf_files/{email}.qr.png','wb') as f:
            f.write(imp_qrcode)
            logger.debug(f"generated qrcode of {email}")
         logger.info(f"generated qrcode of {email}")
  except Exception as e:
    logger.error("Employee with id %s not found",args.id)


def generate_vcard_file(args):
  db_uri = f"postgresql:///{args.dbname}"
  session = models.get_session(db_uri)
  if not os.path.exists('vcf_files'):
    os.mkdir('vcf_files')
  count = 1
  try:
    query = (sa.select
             (models.Employee.lastname,
              models.Employee.firstname,
              models.Designation.title,
              models.Employee.email,
              models.Employee.ph_no)
             .where(models.Employee.title_id==models.Designation.jobid)
             )
    data = session.execute(query).fetchall()
    details = []
    for i in range(0,args.number):
      details.append(data[i])
      for lastname,firstname,title,email,phone_number in details:
          imp_vcard = implement_vcf(lastname,firstname,title,email,phone_number)
          logger.debug("Writing row %d", count)
          count +=1
          with open(f'vcf_files/{email}.vcf','w') as j:
             j.write(imp_vcard)
          if args.qrcode:
             imp_qrcode = implement_qrcode(lastname,firstname,title,email,phone_number)
             logger.debug(f"generating qrcode of {email}")
             with open(f'vcf_files/{email}.qr.png','wb') as f:
               f.write(imp_qrcode)
      logger.info(f"generated qrcode of {email}")
    logger.info(f"generated qrcode of {args.number} employees") 
  except IndexError as e:
    raise HRException ("number of employee out of boundary")


def add_data_to_leaves_table(args):
  db_uri = f"postgresql:///{args.dbname}"
  session = models.get_session(db_uri)
  try:
    insert_info = (models.Leaves(empid=args.employee_id,date=args.date,reason=args.reason))
    session.add(insert_info)
    session.commit()
    logger.info("data inserted to leaves table")
  except (pg.errors.UniqueViolation,sa.exc.IntegrityError) as e:
      raise HRException (e)


def retrieve_data_from_new_table(args):
  db_uri = f"postgresql:///{args.dbname}"
  session = models.get_session(db_uri)
  try:
    retrieve_count = (
                 sa.select
                    (sa.func.count(models.Employee.empid),
                    models.Employee.firstname,
                    models.Employee.lastname,
                    models.Designation.title,
                    models.Employee.email,
                    models.Designation.max_leaves
                    )
                    .where(models.Employee.empid==args.employee_id,
                           models.Designation.jobid==models.Employee.title_id,
                           models.Leaves.empid==models.Employee.empid)
                    .group_by(models.Employee.empid,
                              models.Designation.title,
                              models.Designation.max_leaves)
                  )

    data = session.execute(retrieve_count).fetchall()
    if data != []: 
       for count_serial_number,firstname,lastname,email,designation,num_of_leaves in data:
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
    if data == []:
       query = (
                sa.select
                (models.Designation.max_leaves,
                models.Employee.firstname,
                models.Employee.lastname,
                models.Employee.email,
                models.Designation.title
                )
                .where(models.Employee.empid == args.employee_id,
                       models.Designation.jobid==models.Employee.title_id)
                )
       leaves = session.execute(query).fetchall()
       for num_of_leaves,firstname,lastname,email,designation in leaves:
         d = f"""Name of employee : {firstname} {lastname}
                        Email : {email}
                        Designation : {designation}
                        Maximum alloted leaves : {num_of_leaves}
                        Available leaves : {num_of_leaves}
                        Total leaves taken : 0"""
       print(d) 
  except UnboundLocalError as e:
    raise HRException ("provided employee id is not in tables")

def generate_leave_csv(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)

    with open(f"{args.filename}.csv", "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)

        header = ["Employee_id", "firstname", "lastname", "email", "title", "Total number of leaves", "Leaves left"]
        csv_writer.writerow(header)

        query = (
            sa.select(
                models.Employee.empid,
                models.Employee.firstname,
                models.Employee.lastname,
                models.Employee.email,
                models.Designation.title,
                models.Designation.max_leaves,
                sa.func.count(models.Leaves.empid).label("leave_count")
            )
            .outerjoin(models.Leaves, models.Leaves.empid == models.Employee.empid)
            .where(models.Employee.title_id == models.Designation.jobid)
            .group_by(
                models.Employee.empid,
                models.Employee.firstname,
                models.Employee.lastname,
                models.Employee.email,
                models.Designation.title,
                models.Designation.max_leaves
            )
        )

        results = session.execute(query).fetchall()

        for empid, firstname, lastname, email, title, num_of_leaves, leave_count in results:
            leaves_left = max(num_of_leaves - leave_count, 0)
            row = [empid, firstname, lastname, email, title, num_of_leaves, leaves_left]
            csv_writer.writerow(row)

    logger.info(f"CSV file {args.filename}.csv consisting of employee's leave data is generated")


  #web implementaion starts

def implementing_web(args):
    web.app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql:///{args.dbname}"
    web.db.init_app(web.app)
    web.app.run()  


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
            "genvcard": generate_vcard_file,
            "initleave": add_data_to_leaves_table,
            "retrieve_leave": retrieve_data_from_new_table,
            "retrieve_csv": generate_leave_csv,
            "web"      : implementing_web
        }
        operations[args.subcommand](args)

    except HRException as e:
        logger.error("Program terminated due to %s", e)
        sys.exit(-1)


if __name__ == "__main__":
    main()
