import React from 'react'

function Results(): React.JSX.Element {
  return (
    <section className="tab-pane" aria-label="Results">
      <h2 className="pane-title">Results</h2>
      <p className="pane-subtitle">
        Generated documents will appear here after you upload a profile and analyze a job
        description. Document generation is coming in Phase 3.
      </p>
      <div className="empty-state">
        <p className="empty-state-text">No results yet.</p>
        <p className="empty-state-hint">
          Complete the Profile Upload and Job Description tabs first.
        </p>
      </div>
    </section>
  )
}

export default Results
