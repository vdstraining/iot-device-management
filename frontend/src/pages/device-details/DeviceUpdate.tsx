import React, {useState} from 'react';

export default function UpdateScheduler(){
  const [status,setStatus]=useState('')
  const submit = async (e:any)=>{
    e.preventDefault();
    const body={targets:['device1'], firmware_id:'fw-1', start_time:new Date().toISOString(), rollout_window:60}
    const res = await fetch('/api/firmware/schedules',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    if(res.ok) setStatus('Created')
    else setStatus('Error')
  }
  return (<div><form onSubmit={submit}><button type='submit'>Schedule</button></form><div>{status}</div></div>)
}
