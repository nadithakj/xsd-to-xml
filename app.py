from flask import Flask, request, render_template, send_file, flash, redirect, url_for
import pandas as pd
import io
from lxml import etree

app = Flask(__name__)
app.secret_key = "supersecret"  # Needed for flashing messages

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    # Check if files exist
    if "excel" not in request.files or "xsd" not in request.files:
        flash("Both Excel and XSD files are required.")
        return redirect(url_for("index"))

    excel_file = request.files["excel"]
    xsd_file = request.files["xsd"]

    if excel_file.filename == "" or xsd_file.filename == "":
        flash("Please select both Excel and XSD files.")
        return redirect(url_for("index"))

    try:
        # Read Excel data
        df = pd.read_excel(excel_file)

        # Build XML structure
        root = etree.Element("HolidaysImport", nsmap={None: "http://www.ceridian.com/dbo/HR"})
        holidays = etree.SubElement(root, "Holidays")

        for _, row in df.iterrows():
            holiday = etree.SubElement(holidays, "Holiday")

            date_el = etree.SubElement(holiday, "Date")
            date_el.text = str(row["Date"])

            name_el = etree.SubElement(holiday, "Name")
            name_el.text = str(row["Name"])

        xml_bytes = etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True)

        # ✅ Validate against XSD if requested
        if "validate_flag" in request.form:
            xsd_doc = etree.parse(xsd_file)
            xsd_schema = etree.XMLSchema(xsd_doc)

            xml_doc = etree.fromstring(xml_bytes)
            if not xsd_schema.validate(xml_doc):
                errors = xsd_schema.error_log
                flash(f"XML Validation failed: {errors}")
                return redirect(url_for("index"))

        # Return file for download
        return send_file(
            io.BytesIO(xml_bytes),
            mimetype="application/xml",
            as_attachment=True,
            download_name="output.xml"
        )

    except Exception as e:
        flash(f"Failed to build XML: {e}")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
