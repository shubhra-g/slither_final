import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import { jsPDF } from "jspdf";
import styles from "./analyzer.module.css";
import Button from "./ui/Button";

const SolidityAnalyse = () => {
  const [contractCode, setContractCode] = useState("");
  const [uploadContract, setUploadContract] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onDrop = (acceptedFiles) => {
    setUploadContract(acceptedFiles[0]);
    const reader = new FileReader();
    reader.onload = () => {
      setContractCode(reader.result);
    };
    reader.readAsText(acceptedFiles[0]);
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: ".sol",
  });

  const submitContract = async () => {
    setLoading(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();

      if (uploadContract) {
        // If a file is uploaded
        formData.append("contract_file", uploadContract);
      } else if (contractCode.trim()) {
        // If Solidity code is pasted
        formData.append("contract_code", contractCode.trim());
      } else {
        // If no input is provided
        alert("Please upload a file or paste Solidity code.");
        setLoading(false);
        return;
      }

      // API call to the backend
      const response = await fetch("http://localhost:5000/report", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to analyze: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result); // Save the analysis result to display

      // Open the report in a new window
      openInNewWindow(result); // Pass the result to the new window
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false); // Reset loading state
    }
  };

  const openInNewWindow = (result) => {
    const reportWindow = window.open("", "_blank");

    // Format the result for display
    const formattedResult = JSON.stringify(result, null, 2);

    reportWindow.document.write(
      `<html>
        <head>
          <title>Analysis Report</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              margin: 20px;
              background-color: #f4f7f6;
            }
            h1 {
              color: #333;
            }
            pre {
              background-color: #282c34;
              color: #fff;
              padding: 10px;
              border-radius: 5px;
              font-size: 14px;
              white-space: pre-wrap;
              word-wrap: break-word;
            }
            #download-btn {
              margin-top: 20px;
              padding: 10px 20px;
              background-color: #00FFA3;
              color: white;
              border: none;
              font-size: 16px;
              border-radius: 5px;
              cursor: pointer;
              transition: background-color 0.3s ease;
            }
            #download-btn:hover {
              background-color: #00cc82;
            }
            #download-btn:focus {
              outline: none;
            }
          </style>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        </head>
        <body>
          <h1>Smart Contract Analysis Report</h1>
          <pre>${formattedResult}</pre>
          <button id="download-btn">Download Report</button>
          <script>
            document.getElementById("download-btn").addEventListener("click", function() {
              const { jsPDF } = window.jspdf;
              const doc = new jsPDF();
              doc.setFontSize(12);
              doc.text("Smart Contract Analysis Report", 10, 10);
              doc.text(${JSON.stringify(formattedResult)}, 10, 20);
              doc.save("analysis_report.pdf");
            });
          </script>
        </body>
      </html>`
    );
    reportWindow.document.close();
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>
        ScanSecure <span style={{ color: "#00FFA3" }}>Analyzer</span>
      </h1>
      <p className={styles.description}>
        Paste your smart contract code below or upload a Solidity file to start scanning.
      </p>

      {/* Textarea for pasting Solidity code */}
      <textarea
        className={styles.textArea}
        placeholder="Paste your Solidity contract code here..."
        value={contractCode}
        onChange={(e) => setContractCode(e.target.value)}
      />

      {/* Dropzone for file upload */}
      <div {...getRootProps()} className={styles.dropzone}>
        <input {...getInputProps()} />
        <p>
          Drag & drop your Solidity file here, or{" "}
          <span className={styles.link}>click to upload</span>.
        </p>
        {uploadContract && <p className={styles.fileName}>Uploaded File: {uploadContract.name}</p>}
      </div>

      {/* Submit button */}
      <Button onClick={submitContract} text={loading ? "Scanning..." : "Submit"} disabled={loading} />
    </div>
  );
};

export default SolidityAnalyse;
