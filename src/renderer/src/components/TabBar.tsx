import React from 'react'

interface TabDefinition {
  id: string
  label: string
}

interface TabBarProps {
  tabs: TabDefinition[]
  activeTab: string
  onTabChange: (id: string) => void
}

function TabBar({ tabs, activeTab, onTabChange }: TabBarProps): React.JSX.Element {
  return (
    <nav className="tab-bar" role="tablist" aria-label="Main navigation">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          className={`tab-button ${activeTab === tab.id ? 'tab-button--active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}

export default TabBar
