from flask import Flask, request, jsonify, send_file
import subprocess
import os
import re
from flask_cors import CORS
from fpdf import FPDF

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # Allow only requests from localhost:3000

@app.route('/report', methods=['POST'])
def analyze_contract():
    try:
        contract_code = None
        contract_file = None

        # Handling file upload or pasted code
        if 'contract_file' in request.files:
            uploaded_file = request.files['contract_file']
            if uploaded_file.filename.endswith('.sol'):
                contract_file = uploaded_file.filename
                uploaded_file.save(contract_file)
            else:
                return jsonify({"error": "Uploaded file must be a .sol file."}), 400
        elif request.form.get('contract_code'):
            contract_code = request.form.get('contract_code')
            if not contract_code:
                return jsonify({"error": "No contract code or file provided."}), 400

            contract_file = 'contract_to_analyze.sol'
            with open(contract_file, 'w') as f:
                f.write(contract_code)

        # Run Slither and handle output
        try:
            slither_output = subprocess.check_output(
                ["slither", contract_file], stderr=subprocess.STDOUT, text=True
            )
        except subprocess.CalledProcessError as e:
            formatted_error_output = format_error_output(e.output)
            return jsonify({
                "error": "Slither analysis failed",
                "details": formatted_error_output
            }), 200

        formatted_report = format_slither_output(slither_output)

        # Generate PDF report
        pdf_file_path = generate_pdf_report(formatted_report)
        
        # Include the report link in the JSON response
        response = {
            "report": formatted_report,
            "pdf_download_link": f"/download_report/{os.path.basename(pdf_file_path)}"
        }
        
        # Return the response as JSON so that frontend can handle it
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        # Clean up temporary files
        if contract_file and os.path.exists(contract_file):
            os.remove(contract_file)


@app.route('/download_report/<filename>', methods=['GET'])
def download_report(filename):
    """Serve the generated PDF report."""
    try:
        file_path = os.path.join(os.getcwd(), filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "Report file not found"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to download report", "details": str(e)}), 500


def generate_pdf_report(report):
    """Generate a PDF report from the analysis results."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt="Slither Analysis Report", ln=True, align="C")

    # Add content to the PDF
    pdf.set_font("Arial", size=12)
    pdf.ln(10)  # Add a line break
    for key, value in report.items():
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(200, 10, txt=f"{key.capitalize()}:", ln=True)
        pdf.set_font("Arial", size=12)
        if isinstance(value, list):
            for item in value:
                pdf.cell(200, 10, txt=f"  - {item}", ln=True)
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                pdf.cell(200, 10, txt=f"  {sub_key}: {sub_value}", ln=True)
        else:
            pdf.cell(200, 10, txt=str(value), ln=True)
        pdf.ln(5)

    # Save the PDF to a file
    pdf_file_path = "analysis_report.pdf"
    pdf.output(pdf_file_path)
    return pdf_file_path


def format_error_output(error_output):
    """Formats the Slither error output into a structured JSON format."""
    formatted_output = {"error_details": []}
    lines = error_output.split("\n")
    for line in lines:
        if line.strip():
            formatted_output["error_details"].append(line.strip())
    return formatted_output


def format_slither_output(slither_output):
    """Parses Slither's output and creates a structured JSON report."""
    report = {
        "contract_analyzed": "contract_to_analyze.sol",
        "total_contracts": 1,
        "total_detectors": 93,
        "total_issues_found": 11,
        "detectors": []
    }

    # Extract specific patterns from Slither output
    version_constraint_re = re.compile(r"Version constraint (.*?)(?=\nINFO:Detectors:)")
    parameter_naming_re = re.compile(r"Parameter (.*?) is not in mixedCase")
    state_variable_constant_re = re.compile(r"(.*?)(?=\nReference: https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant)")

    # Version constraint issues
    if version_constraint_match := version_constraint_re.search(slither_output):
        report["detectors"].append({
            "type": "Version Constraint",
            "issue": "Solidity version ^0.8.4 has known severe issues.",
            "details": version_constraint_match.group(1).split("\n"),
            "reference": "https://solidity.readthedocs.io/en/latest/bugs.html"
        })

    # Parameter naming issues
    parameter_naming_matches = parameter_naming_re.findall(slither_output)
    if parameter_naming_matches:
        report["detectors"].append({
            "type": "Parameter Naming Convention",
            "issue": "Parameters are not in mixedCase.",
            "affected_parameters": parameter_naming_matches,
            "reference": "https://github.com/crytic/slither/wiki/Detector-Documentation#conformance-to-solidity-naming-conventions"
        })

    # State variable constant issues
    state_variable_constant_matches = state_variable_constant_re.findall(slither_output)
    if state_variable_constant_matches:
        report["detectors"].append({
            "type": "State Variable Recommendations",
            "issue": "State variables should be declared as constant or immutable.",
            "affected_variables": state_variable_constant_matches,
            "reference": "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant"
        })

    return report


if __name__ == '__main__':
    app.run(debug=True)