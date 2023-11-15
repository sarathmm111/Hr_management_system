import pytest
from v_cards import *


def test_create_v_card():
    lname = "Walker"
    fname = "Steve"
    title = "Accommodation manager"
    email = "teve.walke@hicks.info"
    phone = "(876)953-8282x713"

    vcard = generate_vcard(lname, fname, title, email, phone)

    expected_vcard = f"""BEGIN:VCARD
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

    assert vcard == expected_vcard
