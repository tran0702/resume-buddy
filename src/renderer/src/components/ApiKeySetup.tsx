import React, { useState } from 'react'
import type { AppSettings } from '../env'

interface Props {
  onComplete: () => void
}

export default function ApiKeySetup({ onComplete }: Props): React.JSX.Element {
  const [provider, setProvider] = useState<'gemini' | 'claude'>('gemini')
  const [geminiKey, setGeminiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSave(): Promise<void> {
    const key = provider === 'gemini' ? geminiKey.trim() : anthropicKey.trim()
    if (!key) {
      setError('API key cannot be empty.')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const current = await window.api.loadSettings()
      const updated: AppSettings = {
        ...current,
        aiProvider: provider,
        geminiApiKey: provider === 'gemini' ? geminiKey.trim() : current.geminiApiKey,
        anthropicApiKey: provider === 'claude' ? anthropicKey.trim() : current.anthropicApiKey,
      }

      await window.api.saveSettings(updated)

      const result = await window.api.restartFlask()
      if (!result.ok) {
        setError(
          'Backend did not restart correctly. ' +
          'Check that no other application is using port 5001, then try again.'
        )
        setSaving(false)
        return
      }

      onComplete()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'An unexpected error occurred.')
      setSaving(false)
    }
  }

  return (
    <div className="setup-overlay">
      <div className="setup-modal">
        <h2 className="setup-title">Welcome to Resume Buddy</h2>
        <p className="setup-description">
          Enter your AI provider API key to get started. Keys are stored locally
          on your machine and are never sent to any third-party server.
        </p>

        <div className="setup-field">
          <label className="setup-label">AI Provider</label>
          <select
            className="setup-select"
            value={provider}
            onChange={(e) => setProvider(e.target.value as 'gemini' | 'claude')}
            disabled={saving}
          >
            <option value="gemini">Google Gemini (recommended — free tier available)</option>
            <option value="claude">Anthropic Claude</option>
          </select>
        </div>

        {provider === 'gemini' && (
          <div className="setup-field">
            <label className="setup-label">Gemini API Key</label>
            <input
              className="setup-input"
              type="password"
              placeholder="AIza..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              disabled={saving}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
              autoFocus
            />
            <a
              className="setup-link"
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noreferrer"
            >
              Get a free Gemini API key at aistudio.google.com
            </a>
          </div>
        )}

        {provider === 'claude' && (
          <div className="setup-field">
            <label className="setup-label">Anthropic API Key</label>
            <input
              className="setup-input"
              type="password"
              placeholder="sk-ant-..."
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              disabled={saving}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
              autoFocus
            />
          </div>
        )}

        {error && <p className="setup-error">{error}</p>}

        <button
          className="setup-btn"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Starting backend…' : 'Save & Continue'}
        </button>
      </div>
    </div>
  )
}
