import { useState } from 'react'

export default function FetchOutput() {
  const [agentId, setAgentId] = useState('')
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleFetch() {
    setError('')
    setOutput(null)
    setLoading(true)
    try {
      const resp = await fetch('/api/fetch-output', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ agentId }),
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.error || 'failed')
      setOutput(data.output)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{padding:40,fontFamily:'Arial,Helvetica,sans-serif'}}>
      <h1>Fetch Output</h1>
      <div style={{marginBottom:12}}>
        <input value={agentId} onChange={e=>setAgentId(e.target.value)} placeholder="Enter Agent ID" style={{padding:8,width:320}} />
        <button onClick={handleFetch} style={{marginLeft:12,padding:'8px 12px'}} disabled={loading}>{loading ? 'Fetching...' : 'Fetch Output'}</button>
        {error ? <span style={{color:'crimson',marginLeft:12}}>{error}</span> : null}
      </div>
      {output ? (
        <pre style={{marginTop:24,background:'#f6f6f6',padding:16,borderRadius:8}}>{JSON.stringify(output, null, 2)}</pre>
      ) : null}
    </main>
  )
}
