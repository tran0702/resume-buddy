// TypeScript declarations for window.api (exposed by src/preload/index.ts)

export interface AppSettings {
  aiProvider: 'gemini' | 'claude'
  geminiApiKey: string
  anthropicApiKey: string
  geminiModel: string
  anthropicModel: string
}

declare global {
  interface Window {
    api: {
      platform: string
      loadSettings(): Promise<AppSettings>
      saveSettings(settings: AppSettings): Promise<{ ok: boolean }>
      hasApiKey(): Promise<boolean>
      restartFlask(): Promise<{ ok: boolean }>
    }
  }
}
