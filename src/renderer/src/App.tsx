import React, { useState, useEffect } from 'react'
import TabBar from './components/TabBar'
import ProfileUpload from './components/ProfileUpload'
import JobDescription from './components/JobDescription'
import Results from './components/Results'
import { healthCheck } from './api/client'
import type { MasterProfile, JobAnalysis } from './types/schema'

type Tab = 'profile' | 'job' | 'results'

const TABS: { id: Tab; label: string }[] = [
  { id: 'profile', label: 'Profile Upload' },
  { id: 'job', label: 'Job Description' },
  { id: 'results', label: 'Results' }
]

function App(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('profile')
  const [backendStatus, setBackendStatus] = useState<'checking' | 'ok' | 'error'>('checking')
  const [masterProfile, setMasterProfile] = useState<MasterProfile | null>(null)
  const [jobAnalysis, setJobAnalysis] = useState<JobAnalysis | null>(null)

  useEffect(() => {
    healthCheck().then((result) => {
      setBackendStatus(result.ok ? 'ok' : 'error')
    })
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">Resume Buddy</h1>
        <div className={`backend-status backend-status--${backendStatus}`}>
          {backendStatus === 'checking' && 'Connecting...'}
          {backendStatus === 'ok' && 'Backend Connected'}
          {backendStatus === 'error' && 'Backend Offline'}
        </div>
      </header>

      <TabBar tabs={TABS} activeTab={activeTab} onTabChange={(id) => setActiveTab(id as Tab)} />

      <main className="app-content">
        {activeTab === 'profile' && (
          <ProfileUpload onProfileExtracted={setMasterProfile} />
        )}
        {activeTab === 'job' && (
          <JobDescription onJobAnalyzed={setJobAnalysis} />
        )}
        {activeTab === 'results' && (
          <Results profile={masterProfile} jobAnalysis={jobAnalysis} />
        )}
      </main>
    </div>
  )
}

export default App
