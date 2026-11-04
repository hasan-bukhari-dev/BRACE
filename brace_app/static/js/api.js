export async function request(path,options={}){
 let response;try{response=await fetch(path,options)}catch{throw Error('The local server is unavailable. Restart BRACE and retry. Previously saved results remain on disk; reselect files if this request did not finish.')}
 let data;try{data=await response.json()}catch{throw Error('The server response could not be read. Check the launcher and retry.')}
 if(!response.ok){const d=data.detail;const message=typeof d==='string'?d:d?.message||d?.issues?.map(i=>i.message).join('; ')||(Array.isArray(d)?d.map(i=>i.msg).join('; '):`Request failed (${response.status}).`);const error=Error(message+(d?.next_action?' '+d.next_action:''));error.status=response.status;error.detail=d;throw error}
 return data;
}
