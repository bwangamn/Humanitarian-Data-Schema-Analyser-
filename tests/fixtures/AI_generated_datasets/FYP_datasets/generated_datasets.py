import csv
import json
import os
import random
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd

# Target directory
OUTPUT_DIR = "tests/fixtures/benchmarks"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample domain vocabulary for humanitarian data
ORGS = ["UNICEF", "WFP", "WHO", "UNHCR", "Red Cross", "OXFAM", "IRC", "CARE"]
SECTORS = ["Health", "Nutrition", "WASH", "Protection", "Education", "Shelter", "Logistics"]
PROVINCES = ["Lusaka", "Copperbelt", "Central", "Southern", "Eastern", "Northern"]
DISTRICTS = ["Chisamba", "Chongwe", "Kabwe", "Kitwe", "Ndola", "Monze", "Kafue"]

def rand_date():
    return f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

# -------------------------------------------------------------------
# 1. HXL-CSV (1.0 MB | 12,500 records | 18 fields)
# -------------------------------------------------------------------
def generate_hxl_csv():
    filepath = os.path.join(OUTPUT_DIR, "benchmark_hxl_1mb.csv")
    print(f"Generating {filepath}...")

    headers = [
        "record_id", "country_code", "country_name", "admin1", "admin2",
        "location_lat", "location_lon", "org_name", "sector_name", "target_group",
        "beneficiaries_reached", "funding_usd", "status", "start_date", "end_date",
        "contact_email", "report_period", "remarks"
    ]
    
    hxl_tags = [
        "#meta+id", "#country+code", "#country+name", "#adm1+name", "#adm2+name",
        "#geo+lat", "#geo+lon", "#org+name", "#sector+name", "#group+type",
        "#affected+capacity", "#value+funding", "#status+code", "#date+start", "#date+end",
        "#contact+email", "#date+year", "#meta+remarks"
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(hxl_tags)
        
        for i in range(1, 12501):
            writer.writerow([
                f"REC-{i:06d}", "ZMB", "Zambia", random.choice(PROVINCES), random.choice(DISTRICTS),
                round(random.uniform(-18.0, -8.0), 5), round(random.uniform(22.0, 33.0), 5),
                random.choice(ORGS), random.choice(SECTORS), "IDPs & Host Community",
                random.randint(50, 5000), random.randint(1000, 75000), "Active",
                "2026-01-01", rand_date(), "field_lead@humanitarian.org", "2026-Q2",
                "Regular field operational verification update"
            ])

# -------------------------------------------------------------------
# 2 & 3. Standard CSV (5.0 MB / 62k records / 24 cols & 10.0 MB / 125k records / 32 cols)
# -------------------------------------------------------------------
def generate_standard_csv(filepath, records, num_fields):
    print(f"Generating {filepath}...")
    headers = [f"field_{i+1:02d}" for i in range(num_fields)]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for i in range(1, records + 1):
            row = [f"ID-{i}"]
            for j in range(1, num_fields):
                if j % 4 == 0:
                    row.append(random.choice(ORGS))
                elif j % 4 == 1:
                    row.append(str(random.randint(10, 100000)))
                elif j % 4 == 2:
                    row.append(rand_date())
                else:
                    row.append(f"Standard sample payload string token_{j}")
            writer.writerow(row)

# -------------------------------------------------------------------
# 4. JSON Records (5.0 MB | 45,000 records | 15 fields)
# -------------------------------------------------------------------
def generate_json_records():
    filepath = os.path.join(OUTPUT_DIR, "benchmark_json_5mb.json")
    print(f"Generating {filepath}...")
    
    records = []
    for i in range(1, 45001):
        records.append({
            "record_id": f"JSON-REC-{i:06d}",
            "partner": random.choice(ORGS),
            "sector": random.choice(SECTORS),
            "province": random.choice(PROVINCES),
            "district": random.choice(DISTRICTS),
            "latitude": round(random.uniform(-18.0, -8.0), 4),
            "longitude": round(random.uniform(22.0, 33.0), 4),
            "target_pop": random.randint(100, 10000),
            "reached_pop": random.randint(50, 9500),
            "budget_usd": round(random.uniform(5000.0, 150000.0), 2),
            "is_active": True,
            "start_date": "2026-01-15",
            "end_date": rand_date(),
            "supervisor": "Jane Doe",
            "notes": "Verified field monitoring telemetry record"
        })
        
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

# -------------------------------------------------------------------
# 5. XML IATI Format (5.0 MB | 28,000 records | 20 attributes/elements)
# -------------------------------------------------------------------
def generate_xml_iati():
    filepath = os.path.join(OUTPUT_DIR, "benchmark_iati_5mb.xml")
    print(f"Generating {filepath}...")

    root = ET.Element("iati-activities", version="2.03", generated_datetime="2026-10-15T00:00:00Z")
    
    for i in range(1, 28001):
        act = ET.SubElement(root, "iati-activity")
        ET.SubElement(act, "iati-identifier").text = f"XM-DAC-41121-ACT-{i:06d}"
        
        title = ET.SubElement(act, "title")
        ET.SubElement(title, "narrative", xml_lang="en").text = f"Humanitarian Assistance Project {i}"
        
        description = ET.SubElement(act, "description")
        ET.SubElement(description, "narrative", xml_lang="en").text = "Field response program targeting emergency relief and infrastructure schema profiling."
        
        ET.SubElement(act, "activity-status", code="2")
        
        date = ET.SubElement(act, "activity-date", type="2", iso_date="2026-01-01")
        date.text = "Planned Start Date"
        
        rep_org = ET.SubElement(act, "reporting-org", ref="XM-DAC-41121", type="40")
        ET.SubElement(rep_org, "narrative").text = random.choice(ORGS)
        
        part_org = ET.SubElement(act, "participating-org", ref="ZM-GOV", role="4")
        ET.SubElement(part_org, "narrative").text = "Local Council Authority"
        
        recipient_country = ET.SubElement(act, "recipient-country", code="ZM")
        ET.SubElement(recipient_country, "narrative").text = "Zambia"
        
        sector = ET.SubElement(act, "sector", code="12220", vocabulary="1")
        ET.SubElement(sector, "narrative").text = random.choice(SECTORS)
        
        budget = ET.SubElement(act, "budget", type="1")
        ET.SubElement(budget, "value", currency="USD", value_date="2026-01-01").text = str(random.randint(10000, 250000))
        
        contact = ET.SubElement(act, "contact-info", type="1")
        ET.SubElement(contact, "email").text = "info@humanitarian-iati.org"
        ET.SubElement(contact, "website").text = "https://example.org"

    tree = ET.ElementTree(root)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

# -------------------------------------------------------------------
# 6. XLSForm Excel (2.5 MB | 15,000 survey responses | 45 questions/fields)
# -------------------------------------------------------------------
def generate_xlsform_excel():
    filepath = os.path.join(OUTPUT_DIR, "benchmark_xlsform_2.5mb.xlsx")
    print(f"Generating {filepath}...")

    # Sheet 1: Survey schema definitions (XLSForm standard)
    survey_schema = []
    headers = [f"q_{i+1:02d}" for i in range(45)]
    
    # Building survey definitions
    for col in headers:
        survey_schema.append({"type": "text", "name": col, "label": f"Question Label for {col}", "hint": "Enter response"})

    # Sheet 2: Main data responses (15,000 records across 45 fields)
    data_rows = []
    for i in range(1, 15001):
        row = {"q_01": f"RESP-{i:05d}", "q_02": rand_date(), "q_03": random.choice(PROVINCES), "q_04": random.choice(DISTRICTS)}
        for j in range(5, 46):
            q_key = f"q_{j:02d}"
            row[q_key] = f"Response val {j} - {random.randint(1, 100)}"
        data_rows.append(row)

    df_survey = pd.DataFrame(survey_schema)
    df_data = pd.DataFrame(data_rows)

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df_survey.to_excel(writer, sheet_name='survey', index=False)
        df_data.to_excel(writer, sheet_name='data', index=False)


if __name__ == "__main__":
    generate_hxl_csv()
    generate_standard_csv(os.path.join(OUTPUT_DIR, "benchmark_std_5mb.csv"), 62000, 24)
    generate_standard_csv(os.path.join(OUTPUT_DIR, "benchmark_std_10mb.csv"), 125000, 32)
    generate_json_records()
    generate_xml_iati()
    generate_xlsform_excel()
    print("\n✅ All benchmark datasets generated successfully under tests/fixtures/benchmarks/")