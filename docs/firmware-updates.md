export async function createSchedule(payload:any){
  const res = await fetch('/api/firmware/schedules', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  return res;
}
