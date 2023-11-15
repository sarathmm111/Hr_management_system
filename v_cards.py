import os

import csv


def generate_vcard(lname, fname, title, email, phone):
    vcard = f"""BEGIN:VCARD
VERSION:2.1
N:{lname};{fname}
FN:{fname} {lname}
ORG:Authors, Inc.
TITLE:{title}
TEL;WORK;VOICE:{phone}
ADR;WORK:;;100 Flat Grape Dr.;Fresno;CA;95555;United States of America
EMAIL;PREF;INTERNET:{email}
REV:20150922T195243Z
END:VCARD
"""
    return vcard

def genarate_vcards(output_directory="v_cards"):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open("names.csv", newline="") as csv_file:
        csv_reader = csv.reader(csv_file)
        for lname, fname, title, email, phone in csv_reader:
            vcard = generate_vcard(lname, fname, title, email, phone)
            vcard_filename = f"{fname[:1]}_{lname}.vcf"
            vcard_path = os.path.join(output_directory, vcard_filename)

            with open(vcard_path, "w") as vcard_file:
                vcard_file.write(vcard)
                
if __name__ == "__main__":
    genarate_vcards()


