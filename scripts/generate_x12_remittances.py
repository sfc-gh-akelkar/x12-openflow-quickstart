"""
X12 835 Remittance Generator
Generates realistic HIPAA X12 835 Claim Payment/Advice files for volume testing.

Usage:
    python generate_x12_remittances.py --records 250000 --output volume_835_250k.edi
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

PROCEDURE_CODES = [
    "99201", "99211", "99212", "99213", "99214", "99215",
    "99281", "99282", "99283", "99284", "99381", "99382",
    "36415", "85025", "80053", "80061", "82947", "93000",
    "94640", "71046", "73610", "81001", "90460",
]

ADJUSTMENT_REASONS = ["1", "2", "3", "4", "45", "96", "97", "131", "204", "253"]
ADJUSTMENT_GROUPS = ["CO", "PR", "OA", "PI"]
CLAIM_STATUS_CODES = ["1", "2", "3", "4", "22"]


def generate_remittance(record_num):
    patient_last = random.choice(LAST_NAMES)
    patient_first = random.choice(FIRST_NAMES)
    provider_last = random.choice(LAST_NAMES)
    provider_first = random.choice(FIRST_NAMES)
    provider_npi = f"{random.randint(1000000000, 9999999999)}"

    claim_id = f"CLM{record_num:08d}"
    charge_amount = round(random.uniform(50, 2000), 2)
    payment_pct = random.uniform(0.6, 0.95)
    payment_amount = round(charge_amount * payment_pct, 2)
    patient_resp = round(charge_amount * random.uniform(0.05, 0.2), 2)
    status_code = random.choice(CLAIM_STATUS_CODES)
    payer_control = f"PCN{random.randint(10000000, 99999999)}"

    service_date = datetime(2026, random.randint(1, 12), random.randint(1, 28))
    proc_code = random.choice(PROCEDURE_CODES)
    svc_charge = round(random.uniform(25, 500), 2)
    svc_payment = round(svc_charge * payment_pct, 2)

    adj_group = random.choice(ADJUSTMENT_GROUPS)
    adj_reason = random.choice(ADJUSTMENT_REASONS)
    adj_amount = round(charge_amount - payment_amount - patient_resp, 2)
    if adj_amount < 0:
        adj_amount = round(random.uniform(5, 50), 2)

    allowed = round(payment_amount + patient_resp, 2)

    segments = [
        f"ST*835*{record_num:09d}*005010X221A1",
        f"BPR*I*{payment_amount:.2f}*C*CHK************{service_date.strftime('%Y%m%d')}",
        f"TRN*1*TRN{record_num:08d}*1234567890",
        f"DTM*405*{service_date.strftime('%Y%m%d')}",
        f"N1*PR*PAYER ORGANIZATION*XV*12345",
        f"N1*PE*{provider_last} {provider_first}*XX*{provider_npi}",
        f"CLP*{claim_id}*{status_code}*{charge_amount:.2f}*{payment_amount:.2f}*{patient_resp:.2f}*MC*{payer_control}",
        f"NM1*QC*1*{patient_last}*{patient_first}****MI*MEM{random.randint(100000, 999999)}",
        f"NM1*82*1*{provider_last}*{provider_first}****XX*{provider_npi}",
        f"SVC*HC:{proc_code}*{svc_charge:.2f}*{svc_payment:.2f}**1",
        f"CAS*{adj_group}*{adj_reason}*{adj_amount:.2f}",
        f"DTM*232*{service_date.strftime('%Y%m%d')}",
        f"AMT*AU*{allowed:.2f}",
        f"SE*13*{record_num:09d}",
    ]

    return "~".join(segments) + "~"


def main():
    parser = argparse.ArgumentParser(description="Generate X12 835 remittances for volume testing")
    parser.add_argument("--records", type=int, default=250000, help="Number of remittance records")
    parser.add_argument("--output", type=str, default="volume_835_250k.edi", help="Output filename")
    args = parser.parse_args()

    print(f"Generating {args.records:,} X12 835 remittance records...")

    with open(args.output, "w") as f:
        f.write("ISA*00*          *00*          *ZZ*PAYER          *ZZ*PROVIDER       "
                "*260201*0900*^*00501*000000003*0*P*:~\n")
        f.write("GS*HP*PAYER*PROVIDER*20260201*0900*3*X*005010X221A1~\n")

        for i in range(1, args.records + 1):
            f.write(generate_remittance(i) + "\n")
            if i % 100000 == 0:
                print(f"  ...{i:,} records generated")

        f.write(f"GE*{args.records}*3~\n")
        f.write("IEA*1*000000003~\n")

    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Done. Output: {args.output} ({size_mb:.1f} MB, {args.records:,} records)")


if __name__ == "__main__":
    main()
