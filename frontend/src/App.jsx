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
          <button className="primary">Upload Evidence</button>
          <button className="secondary">Run Test</button>
        </div>
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
    </div>
  );
}
