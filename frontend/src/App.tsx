import { useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'


type Finding = { code?: string; severity: string; message?: string; issue?: string; category?: string; recommendation?: string; evidence?: string }
type Audit = { valid?: boolean; findings?: Finding[]; metadata?: Record<string, unknown> | null; body?: string }

export default function App() {
  const [content, setContent] = useState('')
  const [task, setTask] = useState('')
  const [mode, setMode] = useState<'audit' | 'generate'>('audit')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [validation, setValidation] = useState<Audit | null>(null)
  const [security, setSecurity] = useState<Finding[]>([])
  const [review, setReview] = useState<{ summary?: string; findings?: Finding[]; strengths?: string[] } | null>(null)
  const [notice, setNotice] = useState('')

  async function request(path: string, body: unknown) {
    const response = await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail ?? `Request failed (${response.status})`)
    return data
  }

  async function validateOnly() {
    setBusy(true); setError(''); setNotice('')
    try {
      const data = await request('/api/validate', { content })
      setValidation(data); setSecurity([])
      setReview(null)
      setNotice('Deterministic validation completed.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Validation failed.') }
    finally { setBusy(false) }
  }

  async function audit() {
    setBusy(true); setError(''); setNotice('')
    try {
      const [v, s] = await Promise.all([
        request('/api/validate', { content }),
        request('/api/security-scan', { content }),
      ])
      setValidation(v); setSecurity(s.findings ?? []); setReview(null)
      setNotice('Format validation and heuristic security scan completed.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Audit failed.') }
    finally { setBusy(false) }
  }

  async function reviewSkill() {
    setBusy(true); setError(''); setNotice('')
    try {
      const data = await request('/api/review', { content })
      setValidation(data.validation); setSecurity(data.security ?? []); setReview(data.review)
      setNotice('AI review completed. Treat recommendations as advisory.')
    } catch (e) { setError(e instanceof Error ? e.message : 'AI review failed.') }
    finally { setBusy(false) }
  }

  async function generate() {
    setBusy(true); setError(''); setNotice('')
    try {
      const data = await request('/api/generate', { task })
      setContent(data.content); setValidation(data.validation); setSecurity([]); setReview(null)
      setNotice('Skill generated. Review it, then validate and audit before using it.')
      setMode('audit')
    } catch (e) { setError(e instanceof Error ? e.message : 'Generation failed.') }
    finally { setBusy(false) }
  }

  async function improve() {
    const findings = [
      ...(validation?.findings ?? []).map(f => `${f.severity}: ${f.message ?? f.code}`),
      ...security.map(f => `Security ${f.severity}: ${f.message}`),
      ...(review?.findings ?? []).map(f => `${f.severity}: ${f.issue ?? f.message}. ${f.recommendation ?? ''}`),
    ]
    if (!findings.length) { setError('Run validation, security scan, or AI review first so there are findings to address.'); return }
    setBusy(true); setError(''); setNotice('')
    try {
      const data = await request('/api/improve', { content, findings })
      setContent(data.content); setValidation(data.validation); setSecurity(data.security ?? []); setReview(null)
      setNotice('Improved draft received. Review the content before using it.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Improvement failed.') }
    finally { setBusy(false) }
  }

  function download() {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'SKILL.md'; a.click()
    URL.revokeObjectURL(url)
  }

  const allFindings = [
    ...(validation?.findings ?? []).map(f => ({ ...f, message: f.message ?? f.code ?? 'Finding' })),
    ...security.map(f => ({ ...f, message: f.message ?? 'Security warning' })),
  ]

  return <main className="shell">
    <header className="topbar">
      <div className="brand-mark"><img src="/logo.png" alt="SkillOs logo" /></div>
      <div><h1>SkillOs</h1><p>Agent Skill Workbench</p></div>
      <span className="badge">OPEN SOURCE · MVP</span>
    </header>
    <section className="hero">
      <p className="eyebrow">BUILD · VALIDATE · REVIEW</p>
      <h2>Make agent skills <span>clearer and safer.</span></h2>
      <p className="hero-copy">Create reusable SKILL.md files, validate their structure, inspect suspicious patterns, and use an AI model to review instructions.</p>
    </section>
    <nav className="tabs">
      <button className={mode === 'audit' ? 'active' : ''} onClick={() => setMode('audit')}>Audit a skill</button>
      <button className={mode === 'generate' ? 'active' : ''} onClick={() => setMode('generate')}>Generate a skill</button>
    </nav>
    {mode === 'generate' && <section className="panel generator">
      <label htmlFor="task">What should the skill help an agent do?</label>
      <textarea id="task" value={task} onChange={e => setTask(e.target.value)} rows={4} placeholder="e.g. Review TypeScript pull requests for type safety, error handling, and test coverage." />
      <button className="primary" disabled={busy || task.trim().length < 3} onClick={generate}>{busy ? 'Working…' : 'Generate SKILL.md'}</button>
    </section>}
    <section className="workspace">
      <div className="panel editor-panel">
        <div className="panel-heading"><div><span className="step">01</span><h3>Skill editor</h3></div><span className="muted">Markdown + YAML</span></div>
        <textarea className="code-editor" aria-label="SKILL.md content" value={content} onChange={e => setContent(e.target.value)} spellCheck={false} placeholder={`---
name: your-skill-name
description: One-line description of what this skill helps an agent do.
---

# Skill Title

## Objective
Describe the goal of this skill.

## Workflow
1. Step one...
2. Step two...

## Constraints
- Keep instructions precise and unambiguous.`} />
        <div className="button-row">
          <button disabled={busy} onClick={validateOnly}>Validate</button>
          <button disabled={busy} onClick={audit}>Security scan</button>
          <button disabled={busy} onClick={reviewSkill}>AI review</button>
        </div>
        <div className="button-row bottom-row">
          <button disabled={busy} onClick={improve}>Improve using findings</button>
          <button className="primary" onClick={download}>Download SKILL.md</button>
        </div>
      </div>
      <aside className="results-column">
        <section className="panel">
          <div className="panel-heading"><div><span className="step">02</span><h3>Validation</h3></div>
            {validation && <span className={validation.valid ? 'status good' : 'status bad'}>{validation.valid ? 'VALID' : 'ERRORS'}</span>}
          </div>
          {!validation && <p className="empty">Run validation to inspect the skill format.</p>}
          {validation && <><p className="summary">{validation.valid ? 'No blocking format errors found.' : 'Fix the errors before using this skill.'}</p>
            <FindingList items={validation.findings ?? []} /></>}
        </section>
        <section className="panel">
          <div className="panel-heading"><div><span className="step">03</span><h3>Security heuristics</h3></div><span className="count">{security.length}</span></div>
          {!security.length && <p className="empty">No known patterns flagged, or scan not run. This is not proof that the skill is safe.</p>}
          <FindingList items={security} />
        </section>
        <section className="panel">
          <div className="panel-heading"><div><span className="step">04</span><h3>AI quality review</h3></div></div>
          {!review && <p className="empty">Run AI review to find ambiguity, missing steps, and unclear success criteria.</p>}
          {review && <><p className="summary">{review.summary}</p><FindingList items={(review.findings ?? []).map(f => ({ ...f, message: f.issue ?? f.message ?? 'Finding' }))} />
            {!!review.strengths?.length && <div className="strengths"><strong>Strengths</strong><ul>{review.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></div>}</>}
        </section>
      </aside>
    </section>
    {notice && <div className="notice">{notice}</div>}
    {error && <div className="error" role="alert"><strong>Request failed:</strong> {error}<p>Check that the backend is running and that the configured model endpoint is reachable.</p></div>}
    <footer><span>SkillOs · open-source Agent Skills toolkit</span><span>AI findings are advisory. Never execute untrusted skill scripts.</span></footer>
  </main>
}

function FindingList({ items }: { items: Finding[] }) {
  if (!items.length) return <p className="empty compact">No findings.</p>
  return <ul className="findings">{items.map((f, i) => <li key={`${f.code ?? f.category}-${i}`}>
    <span className={`severity ${f.severity}`}>{f.severity}</span>
    <div><strong>{f.code ?? f.category ?? 'Review finding'}</strong><p>{f.message ?? f.issue}</p>
      {f.recommendation && <p className="recommendation">Fix: {f.recommendation}</p>}
      {f.evidence && <code>{f.evidence}</code>}
    </div>
  </li>)}</ul>
}
