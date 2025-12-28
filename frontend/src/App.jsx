import { useEffect, useRef, useState } from "react";

const features = [
  {
    title: "Evidence Intake",
    description:
      "Upload PBC artifacts and track metadata for each control in a single workspace.",
  },
  {
    title: "Automated Testing",
    description:
      "Trigger AI-assisted attribute testing across occurrence, completeness, and more.",
  },
  {
    title: "Workpaper Output",
    description:
      "Generate a draft memo, tickmarks, and a structured conclusion with a full audit trail.",
  },
];

export default function App() {
  const fileInputRef = useRef(null);
  const [evidence, setEvidence] = useState([]);
  const [uploadState, setUploadState] = useState({ status: "idle", message: "" });

  useEffect(() => {
    fetch("/evidence")
      .then((response) => response.json())
      .then((data) => setEvidence(data))
      .catch(() => setUploadState({ status: "error", message: "Failed to load evidence." }));
  }, []);

  const handlePickFile = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setUploadState({ status: "loading", message: "Uploading..." });
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/evidence/upload", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("Upload failed");
      }
      const payload = await response.json();
      setEvidence((prev) => [payload, ...prev]);
      setUploadState({ status: "success", message: "Upload complete." });
    } catch (error) {
      setUploadState({ status: "error", message: "Upload failed. Try again." });
    } finally {
      event.target.value = "";
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <span className="badge">AuditPilot-SOX MVP</span>
        <h1>AI-Powered SOX Testing Platform</h1>
        <p>
          Centralize evidence, execute automated testing procedures, and deliver
          PCAOB-defendable workpapers in minutes.
        </p>
        <div className="hero-actions">
          <button className="primary" onClick={handlePickFile}>
            Upload Evidence
          </button>
          <button className="secondary">Run Test</button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden-input"
          onChange={handleUpload}
        />
        {uploadState.message && (
          <p className={`status ${uploadState.status}`}>{uploadState.message}</p>
        )}
      </header>

      <section className="grid">
        {features.map((feature) => (
          <article className="card" key={feature.title}>
            <h2>{feature.title}</h2>
            <p>{feature.description}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <div>
          <h2>Control Testing Snapshot</h2>
          <p>
            Link evidence to a control, kick off a test run, and review attribute
            findings before generating a workpaper package.
          </p>
        </div>
        <ul>
          <li>Evidence files ingested: 3</li>
          <li>Controls in review: 2</li>
          <li>Test runs pending review: 1</li>
        </ul>
      </section>

      <section className="evidence">
        <h2>Recent Evidence Uploads</h2>
        {evidence.length === 0 ? (
          <p>No evidence uploaded yet.</p>
        ) : (
          <ul className="evidence-list">
            {evidence.map((item) => (
              <li key={item.id}>
                <div>
                  <strong>{item.filename}</strong>
                  <span>{(item.size_bytes / 1024).toFixed(1)} KB</span>
                  <span>
                    {new Date(item.uploaded_at).toLocaleString()}
                  </span>
                  {item.linked_control_id && (
                    <span>Control: {item.linked_control_id}</span>
                  )}
                </div>
                <a href={`/evidence/${item.id}/download`} className="link">
                  Download
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
