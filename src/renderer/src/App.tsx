import React, { useState, useEffect } from 'react'
import TabBar from './components/TabBar'
import ProfileUpload from './components/ProfileUpload'
import JobDescription from './components/JobDescription'
import Results from './components/Results'
import InterviewPrep from './components/InterviewPrep'
import ApiKeySetup from './components/ApiKeySetup'
import { healthCheck } from './api/client'
import type { MasterProfile, JobAnalysis } from './types/schema'

type Tab = 'profile' | 'job' | 'results' | 'interview'

const TABS: { id: Tab; label: string }[] = [
  { id: 'profile', label: 'Profile Upload' },
  { id: 'job', label: 'Job Description' },
  { id: 'results', label: 'Results' },
  { id: 'interview', label: 'Interview Prep' }
]

function App(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('profile')
  const [backendStatus, setBackendStatus] = useState<'checking' | 'ok' | 'error'>('checking')
  const [masterProfile, setMasterProfile] = useState<MasterProfile | null>(null)
  const [editedProfile, setEditedProfile] = useState<MasterProfile | null>(null)
  const [jobAnalysis, setJobAnalysis] = useState<JobAnalysis | null>(null)
  // null = still checking; true = show setup; false = setup done / not needed
  const [showSetup, setShowSetup] = useState<boolean | null>(null)

  // Check whether an API key has been configured (always true in dev mode)
  useEffect(() => {
    window.api.hasApiKey().then((has) => setShowSetup(!has))
  }, [])

  useEffect(() => {
    healthCheck().then((result) => {
      setBackendStatus(result.ok ? 'ok' : 'error')
    })
  }, [])

  // Called when a new file is uploaded — resets both master and edited profiles
  function handleProfileExtracted(profile: MasterProfile): void {
    setMasterProfile(profile)
    setEditedProfile(profile)
  }

  // Called when the user saves edits in ProfileEditor — only updates the edited copy
  function handleProfileEdited(profile: MasterProfile): void {
    setEditedProfile(profile)
  }

  // Still checking whether setup is needed
  if (showSetup === null) {
    return (
      <div className="app-shell">
        <div className="loading-screen">Loading…</div>
      </div>
    )
  }

  // First run — API key not yet configured
  if (showSetup) {
    return <ApiKeySetup onComplete={() => setShowSetup(false)} />
  }

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
          <ProfileUpload
            onProfileExtracted={handleProfileExtracted}
            currentProfile={editedProfile}
            onProfileEdited={handleProfileEdited}
          />
        )}
        {activeTab === 'job' && (
          <JobDescription onJobAnalyzed={setJobAnalysis} />
        )}
        {activeTab === 'results' && (
          <Results profile={editedProfile} jobAnalysis={jobAnalysis} />
        )}
        {activeTab === 'interview' && (
          <InterviewPrep profile={editedProfile} jobAnalysis={jobAnalysis} />
        )}
      </main>
    </div>
  )
}

export default App
