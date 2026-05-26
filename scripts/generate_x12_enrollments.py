"""
X12 834 Enrollment Generator
Generates realistic HIPAA X12 834 Benefit Enrollment files for volume testing.

Usage:
    python generate_x12_enrollments.py --records 250000 --output volume_834_250k.edi
"""

import argparse
import random
from datetime import datetime, timedelta

LAST_NAMES = ["SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA",
              "MARTINEZ", "HERNANDEZ", "LOPEZ", "GONZALEZ", "DAVIS", "NGUYEN",
              "PATEL", "KIM", "CHEN", "TAYLOR", "ANDERSON", "THOMAS", "JACKSON", "WHITE"]

FIRST_NAMES = ["JAMES", "ROBERT", "MICHAEL", "DAVID", "CARLOS", "JOSE",
               "MARIA", "JESSICA", "SARAH", "EMILY", "ROSA", "ANA",
               "LINH", "PRIYA", "SOFIA", "EMMA", "NOAH", "WILLIAM", "LILY", "MARCUS"]

STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
           "WA", "OR", "CO", "AZ", "MA", "VA", "NJ", "TN", "MN", "WI"]

CITIES = ["PORTLAND", "SEATTLE", "SAN FRANCISCO", "DENVER", "CHICAGO",
           "ATLANTA", "DALLAS", "PHOENIX", "NEW YORK", "MIAMI",
           "BOSTON", "DETROIT", "MINNEAPOLIS", "CHARLOTTE", "AUSTIN"]

PLANS = [
    ("HLT", "GOLD PPO PLAN"),
    ("HLT", "SILVER HMO PLAN"),
    ("HLT", "BRONZE HSA PLAN"),
    ("DEN", "DENTAL PLUS"),
    ("VIS", "VISION BASIC"),
]

MAINTENANCE_TYPES = ["021", "024", "025", "030"]
MAINTENANCE_REASONS = ["AI", "EC", "XN", "01", "28"]
RELATIONSHIP_CODES = ["18", "01", "19"]


def generate_enrollment(record_num):
    last_name = random.choice(LAST_NAMES)
    first_name = random.choice(FIRST_NAMES)
    gender = random.choice(["M", "F"])
    dob = datetime(random.randint(1950, 2010), random.randint(1, 12), random.randint(1, 28))
    state = random.choice(STATES)
    city = random.choice(CITIES)
    zipcode = f"{random.randint(10000, 99999)}"
    member_id = f"SSN{record_num:06d}"
    maint_type = random.choice(MAINTENANCE_TYPES)
    maint_reason = random.choice(MAINTENANCE_REASONS)
    rel_code = random.choice(RELATIONSHIP_CODES)
    plan = random.choice(PLANS)
    coverage_start = datetime(2026, random.randint(1, 12), 1)
    coverage_end = coverage_start + timedelta(days=365)
    emp_date = coverage_start - timedelta(days=random.randint(30, 365))
    benefit_status = "Y" if maint_type in ["021", "024"] else "N"
    emp_status = random.choice(["AC", "FT", "PT", "RT", "TE"])

    segments = [
        f"ST*834*{record_num:09d}*005010X220A1",
        f"BGN*00*REF{record_num:08d}*{coverage_start.strftime('%Y%m%d')}*0800****2",
        f"INS*{benefit_status}*{rel_code}*{maint_type}*{maint_reason}*A***{emp_status}",
        f"REF*0F*{member_id}",
        f"DTP*336*D8*{emp_date.strftime('%Y%m%d')}",
        f"DTP*348*D8*{coverage_start.strftime('%Y%m%d')}",
        f"DTP*349*D8*{coverage_end.strftime('%Y%m%d')}",
        f"NM1*IL*1*{last_name}*{first_name}****34*{member_id}",
        f"N3*{random.randint(100, 9999)} {random.choice(['MAIN', 'OAK', 'ELM', 'PINE', 'MAPLE'])} ST",
        f"N4*{city}*{state}*{zipcode}",
        f"DMG*D8*{dob.strftime('%Y%m%d')}*{gender}",
        f"HD*{maint_type}**{plan[0]}*{plan[1]}*EMP",
        f"SE*12*{record_num:09d}",
    ]

    return "~".join(segments) + "~"


def main():
    parser = argparse.ArgumentParser(description="Generate X12 834 enrollments for volume testing")
    parser.add_argument("--records", type=int, default=250000, help="Number of enrollment records")
    parser.add_argument("--output", type=str, default="volume_834_250k.edi", help="Output filename")
    args = parser.parse_args()

    print(f"Generating {args.records:,} X12 834 enrollment records...")

    with open(args.output, "w") as f:
        f.write("ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
                "*260115*0800*^*00501*000000002*0*P*:~\n")
        f.write("GS*BE*SENDER*RECEIVER*20260115*0800*2*X*005010X220A1~\n")

        for i in range(1, args.records + 1):
            f.write(generate_enrollment(i) + "\n")
            if i % 100000 == 0:
                print(f"  ...{i:,} records generated")

        f.write(f"GE*{args.records}*2~\n")
        f.write("IEA*1*000000002~\n")

    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Done. Output: {args.output} ({size_mb:.1f} MB, {args.records:,} records)")


if __name__ == "__main__":
    main()
