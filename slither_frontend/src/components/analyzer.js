import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
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
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false); // Reset loading state
    }
  };

  return (
    <>
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

        {/* Displaying analysis results */}
        {analysisResult && (
          <div className={styles.result}>
            <h2>Analysis Report</h2>
            <pre>{JSON.stringify(analysisResult, null, 2)}</pre>
          </div>
        )}
      </div>
    </>
  );
};

export default SolidityAnalyse;
