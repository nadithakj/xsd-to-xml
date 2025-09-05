from flask import Flask, request, render_template, send_file
import pandas as pd
import xml.etree.ElementTree as ET
import io
import datetime

app = Flask(__name__)

def create_element(parent, tag, value):
    """Helper to safely create XML child element"""
    elem = ET.SubElement(parent, tag)
    if pd.notna(value):  # only set if not NaN
        elem.text = str(value)
    return elem

def build_xml_from_excel(excel_file):
    # Read all sheets
    xls = pd.ExcelFile(excel_file)

    root = ET.Element("Holidays")  # Root element

    # === Holiday Sheet ===
    if "Holiday" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="Holiday")
        for _, row in df.iterrows():
            holiday = ET.SubElement(root, "Holiday")
            create_element(holiday, "Name", row.get("Name"))
            create_element(holiday, "Description", row.get("Description"))
            
            # Ensure HolidayDate is formatted as YYYY-MM-DD
            holiday_date = row.get("HolidayDate")
            if pd.notna(holiday_date):
                if isinstance(holiday_date, (datetime.date, datetime.datetime)):
                    holiday_date = holiday_date.strftime("%Y-%m-%d")
            create_element(holiday, "HolidayDate", holiday_date)

            create_element(holiday, "XRefCode", row.get("XRefCode"))
            create_element(holiday, "IsBankHoliday", str(row.get("IsBankHoliday")).lower())

    # === HolidayGroup Sheet ===
    if "HolidayGroup" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="HolidayGroup")
        for _, row in df.iterrows():
            group = ET.SubElement(root, "HolidayGroup")
            create_element(group, "Name", row.get("Name"))
            create_element(group, "Description", row.get("Description"))
            create_element(group, "XRefCode", row.get("XRefCode"))
            create_element(group, "GeoCountry", row.get("GeoCountry"))

            # Org can be multiple → comma separated
            orgs = str(row.get("OrgXref")).split(",") if pd.notna(row.get("OrgXref")) else []
            for org in orgs:
                org_elem = ET.SubElement(group, "Org")
                create_element(org_elem, "OrgXref", org.strip())

    # === HolidayGroupList Sheet ===
    if "HolidayGroupList" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="HolidayGroupList")
        for _, row in df.iterrows():
            hgl = ET.SubElement(root, "HolidayGroupList")
            create_element(hgl, "HolidayGroupXRef", row.get("HolidayGroupXRef"))
            create_element(hgl, "HolidayXRef", row.get("HolidayXRef"))

    return ET.ElementTree(root)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400

        file = request.files["file"]

        try:
            xml_tree = build_xml_from_excel(file)
            xml_bytes = io.BytesIO()
            xml_tree.write(xml_bytes, encoding="utf-8", xml_declaration=True)
            xml_bytes.seek(0)

            return send_file(
                xml_bytes,
                as_attachment=True,
                download_name="Holidays.xml",
                mimetype="application/xml",
            )
        except Exception as e:
            return f"Failed to build XML: {str(e)}", 500

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
