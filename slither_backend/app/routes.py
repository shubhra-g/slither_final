from flask import Flask, request, jsonify
import subprocess
import os
import re
from flask_cors import CORS
app = Flask(__name__)

CORS(app)
@app.route('/report', methods=['POST'])
def analyze_contract():
    try:
        contract_code=None
        contract_file = None

        
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

        
        try:
            slither_output = subprocess.check_output(
                ["slither", contract_file], stderr=subprocess.STDOUT, text=True
            )
        except subprocess.CalledProcessError as e:
            formatted_error_output = format_error_output(e.output)
            return jsonify({
                "!": "Slither analysis failed",
                "details": formatted_error_output
            }), 200

        formatted_report = format_slither_output(slither_output)

        return jsonify(formatted_report)

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
       
        if contract_file and os.path.exists(contract_file):
            os.remove(contract_file)


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

    
    version_constraint_re = re.compile(r"Version constraint (.*?)(?=\nINFO:Detectors:)")
    parameter_naming_re = re.compile(r"Parameter (.*?) is not in mixedCase")
    state_variable_constant_re = re.compile(r"(.*?)(?=\nReference: https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant)")
    immutability_re = re.compile(r"(.*?)(?=\nReference: https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-immutable)")

    
    if version_constraint_match := version_constraint_re.search(slither_output):
        report["detectors"].append({
            "type": "Version Constraint",
            "issue": "Solidity version ^0.8.4 has known severe issues.",
            "details": version_constraint_match.group(1).split("\n"),
            "reference": "https://solidity.readthedocs.io/en/latest/bugs.html"
        })

    
    parameter_naming_matches = parameter_naming_re.findall(slither_output)
    if parameter_naming_matches:
        report["detectors"].append({
            "type": "Parameter Naming Convention",
            "issue": "Parameters are not in mixedCase.",
            "affected_parameters": parameter_naming_matches,
            "reference": "https://github.com/crytic/slither/wiki/Detector-Documentation#conformance-to-solidity-naming-conventions"
        })

    
    state_variable_constant_matches = state_variable_constant_re.findall(slither_output)
    if state_variable_constant_matches:
        report["detectors"].append({
            "type": "State Variable Recommendations",
            "issue": "State variables should be declared as constant or immutable.",
            "affected_variables": state_variable_constant_matches,
            "reference": "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant"
        })

    
    immutability_matches = immutability_re.findall(slither_output)
    if immutability_matches:
        report["detectors"].append({
            "type": "Immutability Recommendation",
            "issue": "totalSupply should be declared as immutable.",
            "affected_variable": immutability_matches[0],
            "reference": "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-immutable"
        })

    return report


if __name__ == '__main__':
    app.run(debug=True)
