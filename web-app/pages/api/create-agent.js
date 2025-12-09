import fs from 'fs'
import path from 'path'
const API_URL = "https://api.bey.dev/v1";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const apiKey = process.env.BEY_API_KEY;
  if (!apiKey) return res.status(500).json({ error: "Missing BEY_API_KEY on server" });

  const { roleName, roleDescription, candidateName, avatarId, memory } = req.body || {};
  if (!roleName || !roleDescription || !candidateName) {
    return res.status(400).json({ error: "roleName, roleDescription and candidateName are required" });
  }

  
  let promptPath = path.resolve(process.cwd(), 'agent', 'system_prompt.txt')
  if (!fs.existsSync(promptPath)) {

    promptPath = path.resolve(process.cwd(), '..', 'agent', 'system_prompt.txt')
  }
  let systemPrompt = null
  try {
    systemPrompt = fs.readFileSync(promptPath, 'utf8')

    const memoryStr = memory ? JSON.stringify(memory) : '[]'
    systemPrompt = systemPrompt.replace('{memory}', memoryStr).replace('{role_name}', roleName).replace('{role_description}', roleDescription).replace('{candidate_name}', candidateName)
    
    systemPrompt = systemPrompt.replace(/{{/g, '{').replace(/}}/g, '}')
  } catch (e) {
    console.error('Failed reading system prompt:', e)
    systemPrompt = `Ava: ${roleName} Recruiter for ${candidateName}`
  }

  
  const DEFAULT_AVATAR_ID = 'b9be11b8-89fb-4227-8f86-4a881393cbdb'
  const effectiveAvatarId = avatarId || DEFAULT_AVATAR_ID

  try {
    const resp = await fetch(`${API_URL}/agent`, {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        name: `${roleName} Recruiter for ${candidateName}`,
        system_prompt: systemPrompt,
        greeting: `Hello ${candidateName}, how are you doing? Are you ready to discuss the candidate requirements?`,
        avatar_id: effectiveAvatarId,
      }),
    });

    const data = await resp.json();
    if (!resp.ok) {

      const upstreamMessage = data && (data.error || data.message || data.detail)
        ? (data.error || data.message || data.detail)
        : JSON.stringify(data);
      return res.status(resp.status).json({ error: String(upstreamMessage) });
    }

    return res.status(200).json({ agentId: data.id, agentName: data.name });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: String(err) });
  }
}
