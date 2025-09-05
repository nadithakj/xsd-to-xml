import os
import tempfile
import pandas as pd
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from lxml import etree as ET
import xmlschema

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
# Limit uploads (adjust if needed)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "50")) * 1024 * 1024

def build_xml_from_df(df: pd.DataFrame, root_name: str, row_name: str) -> ET._ElementTree:
    root = ET.Element(root_name)
    # NaN-safe conversion and tag sanitization
    for _, row in df.iterrows():
        row_elem = ET.SubElement(root, row_name)
        for col in df.columns:
            tag = str(col).strip().replace(" ", "_")
            value = row[col]
            if pd.isna(value):
                continue
            child = ET.SubElement(row_elem, tag)
            child.text = str(value)
    return ET.ElementTree(root)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    if "xsd" not in request.files or "excel" not in request.files:
        flash("Please upload both an XSD and an Excel file.")
        return redirect(url_for("index"))

    xsd_file = request.files["xsd"]
    excel_file = request.files["excel"]
    row_element = request.form.get("row_element", "Record").strip() or "Record"
    root_element_override = request.form.get("root_element", "").strip()
    validate_flag = request.form.get("validate_flag", "on") == "on"

    # Use a temp working directory to avoid persistence concerns
    with tempfile.TemporaryDirectory() as tmpdir:
        xsd_path = os.path.join(tmpdir, xsd_file.filename or "schema.xsd")
        excel_path = os.path.join(tmpdir, excel_file.filename or "data.xlsx")
        xsd_file.save(xsd_path)
        excel_file.save(excel_path)

        # Load schema
        try:
            schema = xmlschema.XMLSchema(xsd_path)
        except Exception as e:
            flash(f"Failed to parse XSD: {e}")
            return redirect(url_for("index"))

        # Decide root element
        if root_element_override:
            root_element = root_element_override
        else:
            # first global element from XSD
            try:
                root_element = list(schema.elements.keys())[0]
            except Exception:
                flash("Could not determine root element from the XSD. Please enter it manually.")
                return redirect(url_for("index"))

        # Read Excel
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            flash(f"Failed to read Excel file: {e}")
            return redirect(url_for("index"))

        # Build XML
        try:
            tree = build_xml_from_df(df, root_element, row_element)
        except Exception as e:
            flash(f"Failed to build XML: {e}")
            return redirect(url_for("index"))

        out_path = os.path.join(tmpdir, "output.xml")
        tree.write(out_path, xml_declaration=True, encoding="utf-8", pretty_print=True)

        # Validate (optional)
        if validate_flag:
            try:
                schema.validate(out_path)
            except Exception as e:
                # On validation error, show the first line to user; full logs would be too long
                flash(f"XML did not validate against the XSD. Error: {str(e)}")
                return redirect(url_for("index"))

        # Send file
        return send_file(out_path, as_attachment=True, download_name="output.xml")

if __name__ == "__main__":
    # For local testing only; Render will use gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
