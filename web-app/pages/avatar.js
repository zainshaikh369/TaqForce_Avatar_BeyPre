import { useState } from 'react'

export default function UseExistingAvatar() {
  const [avatarId, setAvatarId] = useState('')
  const [embedUrl, setEmbedUrl] = useState('')
  const [error, setError] = useState('')

  function handleUseAvatar() {
    if (!avatarId) {
      setError('Please enter an avatar ID')
      return
    }
    setEmbedUrl(`https://bey.chat/${avatarId}`)
    setError('')
  }

  return (
    <main style={{padding:40,fontFamily:'Arial,Helvetica,sans-serif'}}>
      <h1>Use Existing Avatar</h1>
      <div style={{marginBottom:12}}>
        <input value={avatarId} onChange={e=>setAvatarId(e.target.value)} placeholder="Enter Avatar ID" style={{padding:8,width:320}} />
        <button onClick={handleUseAvatar} style={{marginLeft:12,padding:'8px 12px'}}>Use Avatar</button>
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
    </main>
  )
}
