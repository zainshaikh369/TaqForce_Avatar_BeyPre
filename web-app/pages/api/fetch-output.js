const API_URL = "https://api.bey.dev/v1";

function tryParseJSON(s) {
  try {
    return JSON.parse(s);
  } catch (e) {
    return null;
  }
}

function extractJsonFromText(text) {
  if (!text) return null;
  // try markers / fences
  const patterns = [
    /OUTPUT_JSON_START\s*(\{[\s\S]*?\})\s*OUTPUT_JSON_END/,
    /```json\s*(\{[\s\S]*?\})\s*```/,
    /(\{\s*"role"[\s\S]*?\})/,
  ];
  for (const pat of patterns) {
    const m = text.match(pat);
    if (m && m[1]) {
      const cand = m[1].replace(/`/g, "").trim();
      const parsed = tryParseJSON(cand);
      if (parsed) return parsed;
      // try to remove trailing commas quickly
      const cleaned = cand.replace(/,\s*}\s*$/m, "}").replace(/,\s*\]\s*$/m, "]");
      const parsed2 = tryParseJSON(cleaned);
      if (parsed2) return parsed2;
    }
  }

  // fallback: find balanced {...} or [...] blocks
  const opens = [['{','}'], ['[',']']];
  for (const [open, close] of opens) {
    for (let i = 0; i < text.length; i++) {
      if (text[i] !== open) continue;
      let depth = 0;
      for (let j = i; j < text.length; j++) {
        if (text[j] === open) depth++;
        else if (text[j] === close) depth--;
        if (depth === 0) {
          const cand = text.slice(i, j+1);
          const parsed = tryParseJSON(cand);
          if (parsed) return parsed;
          const cleaned = cand.replace(/,\s*}\s*$/m, "}").replace(/,\s*\]\s*$/m, "]");
          const parsed2 = tryParseJSON(cleaned);
          if (parsed2) return parsed2;
          break;
        }
      }
    }
  }
  return null;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const apiKey = process.env.BEY_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'Missing BEY_API_KEY on server' });

  const { agentId } = req.body || {};
  if (!agentId) return res.status(400).json({ error: 'agentId required in body' });

  try {
    const callsResp = await fetch(`${API_URL}/calls`, { headers: { 'x-api-key': apiKey } });
    if (!callsResp.ok) {
      const body = await callsResp.text();
      return res.status(502).json({ error: `Failed fetching calls: ${callsResp.status}`, detail: body });
    }
    const callsJson = await callsResp.json();
    const calls = callsJson.data || [];
    // find latest ended call for this agent
    const endedCalls = calls.filter(c => c.agent_id === agentId && c.ended_at).sort((a,b)=> new Date(b.ended_at) - new Date(a.ended_at));
    if (endedCalls.length === 0) return res.status(404).json({ error: 'No ended calls found for agent' });
    const call = endedCalls[0];

    const messagesResp = await fetch(`${API_URL}/calls/${call.id}/messages`, { headers: { 'x-api-key': apiKey } });
    if (!messagesResp.ok) {
      const body = await messagesResp.text();
      return res.status(502).json({ error: `Failed fetching messages: ${messagesResp.status}`, detail: body });
    }
    const messages = await messagesResp.json();

    // prefer assistant messages in reverse
    let result = null;
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      const sender = (msg.sender || '').toLowerCase();
      if (['assistant','ai','bot'].includes(sender)) {
        const parsed = extractJsonFromText(msg.message || '');
        if (parsed) { result = { parsed, from: msg }; break; }
      }
    }
    if (!result) {
      const full = messages.map(m => m.message || '').join('\n\n');
      const parsed = extractJsonFromText(full);
      if (parsed) result = { parsed, from: null };
    }

    if (!result) return res.status(404).json({ error: 'No structured JSON found in messages', messages });

    return res.status(200).json({ callId: call.id, output: result.parsed });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ error: String(e) });
  }
}
