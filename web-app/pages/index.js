import { useState } from 'react'
import Link from 'next/link'

export default function Home() {
  const [tab, setTab] = useState('create')
  const [roleName, setRoleName] = useState('Recruiter')
  const [roleDescription, setRoleDescription] = useState('Hiring Senior Java dev')
  const [candidateName, setCandidateName] = useState('Acme')
  const [loading, setLoading] = useState(false)
  const [embedUrl, setEmbedUrl] = useState('')
  const [error, setError] = useState('')
  const MALE_AVATAR = 'b9be11b8-89fb-4227-8f86-4a881393cbdb'
  const FEMALE_AVATAR = '70b1b917-ed16-4531-bb6c-b0bdb79449b4'
  const [avatarId, setAvatarId] = useState(MALE_AVATAR)

  async function startSession() {
    setLoading(true)
    setError('')
    try {
      const resp = await fetch('/api/create-agent', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ roleName, roleDescription, candidateName, avatarId }),
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.error || 'failed')
      setEmbedUrl(`https://bey.chat/${data.agentId}`)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{padding:40,fontFamily:'Arial,Helvetica,sans-serif'}}>
      <h1>Bey Avatar Portal</h1>
      <div style={{display:'flex',gap:16,marginBottom:32}}>
        <button onClick={()=>setTab('create')} style={{padding:'8px 16px',background:tab==='create'?'#222':'#eee',color:tab==='create'?'#fff':'#222',border:'none',borderRadius:4}}>Create New Avatar</button>
        <button onClick={()=>setTab('use')} style={{padding:'8px 16px',background:tab==='use'?'#222':'#eee',color:tab==='use'?'#fff':'#222',border:'none',borderRadius:4}}>Use Existing Avatar</button>
        <button onClick={()=>setTab('fetch')} style={{padding:'8px 16px',background:tab==='fetch'?'#222':'#eee',color:tab==='fetch'?'#fff':'#222',border:'none',borderRadius:4}}>Fetch Output</button>
      </div>
      {tab==='create' && (
        <div>
          <h2>Create New Avatar</h2>
          <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:12}}>
            <input value={roleName} onChange={(e)=>setRoleName(e.target.value)} placeholder="Role name" style={{padding:8,width:220}} />
            <input value={candidateName} onChange={(e)=>setCandidateName(e.target.value)} placeholder="Candidate name" style={{padding:8,width:220}} />
          </div>
          <div style={{marginBottom:12}}>
            <input value={roleDescription} onChange={(e)=>setRoleDescription(e.target.value)} placeholder="Role description" style={{padding:8,width:460}} />
          </div>
          <div style={{marginBottom:12}}>
            <label style={{marginRight:12}}>Choose avatar:</label>
            <label style={{marginRight:12}}>
              <input type="radio" name="avatar" value={MALE_AVATAR} checked={avatarId===MALE_AVATAR} onChange={()=>setAvatarId(MALE_AVATAR)} /> Male
            </label>
            <label>
              <input type="radio" name="avatar" value={FEMALE_AVATAR} checked={avatarId===FEMALE_AVATAR} onChange={()=>setAvatarId(FEMALE_AVATAR)} /> Female
            </label>
          </div>
          <div>
            <button onClick={startSession} style={{padding:'8px 12px'}} disabled={loading}>{loading? 'Starting...' : 'Start Session'}</button>
            {error ? <span style={{color:'crimson',marginLeft:12}}>{error}</span> : null}
          </div>
          {embedUrl ? (
            <div style={{marginTop:20}}>
              <h2>Live Session</h2>
              <div style={{width:'100%',height:600,borderRadius:8,overflow:'hidden',boxShadow:'0 8px 24px rgba(0,0,0,.12)'}}>
                <iframe
                  src={embedUrl}
                  title="Bey Avatar"
                  style={{width:'100%',height:'100%',border:0}}
                  allow="camera; microphone; autoplay; encrypted-media; fullscreen"
                  allowFullScreen
                />
              </div>
            </div>
          ) : null}
        </div>
      )}
      {tab==='use' && (
        <iframe src="/avatar" style={{width:'100%',height:700,border:0}} title="Use Existing Avatar" />
      )}
      {tab==='fetch' && (
        <iframe src="/fetch-output" style={{width:'100%',height:700,border:0}} title="Fetch Output" />
      )}
    </main>
  )
}
