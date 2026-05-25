"""
X12 837P Claims Generator
Generates realistic HIPAA X12 837 Professional Claims for volume testing.

Usage:
    python generate_x12_claims.py --claims 500000 --output volume_837p_500k.edi
"""

import argparse
import random
import string
from datetime import datetime, timedelta

PROVIDERS = [
    ("ACME HEALTH CLINIC", "1234567890"),
    ("RIVERSIDE PEDIATRICS", "9876543210"),
    ("SUMMIT FAMILY MEDICINE", "1112223333"),
    ("COASTAL URGENT CARE", "4445556666"),
    ("METRO GENERAL HOSPITAL", "5556667777"),
    ("PINE VALLEY MEDICAL", "6667778888"),
    ("LAKESHORE HEALTH CENTER", "7778889999"),
]

PAYERS = [
    ("BLUE CROSS BLUE SHIELD", "54321"),
    ("UNITED HEALTHCARE", "86111"),
    ("AETNA", "67890"),
    ("CIGNA", "77788"),
    ("HUMANA", "99887"),
]

LAST_NAMES = ["SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA",
              "MARTINEZ", "HERNANDEZ", "LOPEZ", "GONZALEZ", "DAVIS", "NGUYEN",
              "PATEL", "KIM", "CHEN", "TAYLOR", "ANDERSON", "THOMAS", "JACKSON", "WHITE"]

FIRST_NAMES = ["JAMES", "ROBERT", "MICHAEL", "DAVID", "CARLOS", "JOSE",
               "MARIA", "JESSICA", "SARAH", "EMILY", "ROSA", "ANA",
               "LINH", "PRIYA", "SOFIA", "EMMA", "NOAH", "WILLIAM", "LILY", "MARCUS"]

PROCEDURE_CODES = [
    ("99201", 150, 600), ("99211", 50, 150), ("99212", 100, 250),
    ("99213", 150, 350), ("99214", 200, 450), ("99215", 250, 600),
    ("99281", 100, 250), ("99282", 150, 350), ("99283", 200, 500),
    ("99284", 300, 700), ("99381", 150, 400), ("99382", 150, 400),
    ("99392", 150, 350), ("36415", 25, 75), ("85025", 25, 75),
    ("80053", 40, 120), ("80061", 50, 150), ("82947", 20, 60),
    ("83036", 30, 80), ("87880", 15, 50), ("90460", 40, 100),
    ("90471", 20, 60), ("90714", 30, 80), ("93000", 80, 200),
    ("94640", 60, 150), ("71046", 100, 300), ("73610", 100, 300),
    ("73600", 80, 250), ("99070", 10, 50), ("81001", 10, 40),
]

ICD10_CODES = [
    "J06.9", "J20.9", "J45.20", "R05.9", "I10", "E11.9",
    "M79.3", "N39.0", "R10.9", "K21.0", "Z00.129", "Z23",
    "H66.90", "L30.9", "S93.401A", "J02.9", "R50.9", "K59.00",
]

PLACE_OF_SERVICE = ["11", "22", "23"]


def generate_claim(claim_num):
    provider = random.choice(PROVIDERS)
    payer = random.choice(PAYERS)
    last_name = random.choice(LAST_NAMES)
    first_name = random.choice(FIRST_NAMES)
    gender = random.choice(["M", "F"])
    dob = datetime(random.randint(1950, 2023), random.randint(1, 12), random.randint(1, 28))
    service_date = datetime(2026, random.randint(1, 12), random.randint(1, 28))
    claim_date = service_date - timedelta(days=random.randint(1, 30))
    member_id = f"MEM{random.randint(100000, 999999)}"
    claim_id = f"CLM{claim_num:08d}"
    pos = random.choice(PLACE_OF_SERVICE)
    icd10 = random.choice(ICD10_CODES)

    num_lines = random.randint(1, 5)
    selected_procs = random.sample(PROCEDURE_CODES, min(num_lines, len(PROCEDURE_CODES)))
    service_lines = []
    total = 0.0
    for i, (code, low, high) in enumerate(selected_procs, 1):
        charge = round(random.uniform(low, high), 2)
        total += charge
        service_lines.append(
            f"SV1*HC:{code}*{charge:.2f}*UN*1***1~"
            f"DTP*472*D8*{service_date.strftime('%Y%m%d')}~"
            f"REF*6R*LN{i:03d}"
        )

    rendering_last = random.choice(LAST_NAMES)
    seg_count = 18 + (num_lines * 3)

    segments = [
        f"ST*837*{claim_num:09d}*005010X222A1",
        f"BHT*0019*00*{claim_id}*{claim_date.strftime('%Y%m%d')}*1030*CH",
        f"NM1*41*2*{provider[0]}*****46*{provider[1]}",
        f"PER*IC*BILLING DEPT*TE*5551234567",
        f"NM1*40*2*{payer[0]}*****46*{payer[1]}",
        f"HL*1**20*1",
        f"NM1*85*2*{provider[0]}*****XX*{provider[1]}",
        f"N3*100 MAIN ST",
        f"N4*ANYTOWN*CA*90210",
        f"REF*EI*{random.randint(100000000, 999999999)}",
        f"HL*2*1*22*1",
        f"NM1*IL*1*{last_name}*{first_name}****MI*{member_id}",
        f"N3*{random.randint(100, 9999)} MAIN ST",
        f"N4*ANYTOWN*CA*90210",
        f"DMG*D8*{dob.strftime('%Y%m%d')}*{gender}",
        f"HL*3*2*23*0",
        f"NM1*82*1*{rendering_last}{rendering_last}****XX*{provider[1]}",
        f"PRV*PE*PXC*208000000X",
    ]

    for sl in service_lines:
        segments.append(sl)

    segments.extend([
        f"CLM*{claim_id}*{total:.2f}***{pos}:B:1*Y*A*Y*Y",
        f"HI*ABK:{icd10}",
        f"SE*{seg_count}*{claim_num:09d}",
    ])

    return "~".join(segments) + "~"


def main():
    parser = argparse.ArgumentParser(description="Generate X12 837P claims for volume testing")
    parser.add_argument("--claims", type=int, default=1000, help="Number of claims to generate")
    parser.add_argument("--output", type=str, default="volume_837p.edi", help="Output filename")
    args = parser.parse_args()

    print(f"Generating {args.claims:,} X12 837P claims...")

    with open(args.output, "w") as f:
        f.write("ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
                "*260101*1030*^*00501*000000001*0*P*:~\n")
        f.write("GS*HC*SENDER*RECEIVER*20260101*1030*1*X*005010X222A1~\n")

        for i in range(1, args.claims + 1):
            f.write(generate_claim(i) + "\n")
            if i % 100000 == 0:
                print(f"  ...{i:,} claims generated")

        f.write(f"GE*{args.claims}*1~\n")
        f.write("IEA*1*000000001~\n")

    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Done. Output: {args.output} ({size_mb:.1f} MB, {args.claims:,} claims)")


if __name__ == "__main__":
    main()
