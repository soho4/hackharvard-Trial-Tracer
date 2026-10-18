/* Read-only report contract. No date-window detector is implemented here. */
(function(root){
'use strict';
const STATUSES=['PASS','POTENTIAL_DEVIATION','DATA_QUERY','NOT_EVALUABLE'];
const obj=v=>v!==null && typeof v==='object' && !Array.isArray(v);
const text=v=>typeof v==='string' && v.trim().length>0;
const sha=v=>typeof v==='string' && /^[0-9a-f]{64}$/.test(v);
function validDate(v){
 if(typeof v!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(v))return false;
 const d=new Date(v+'T00:00:00Z'); return !Number.isNaN(d.getTime()) && d.toISOString().slice(0,10)===v;
}
function validateBundle(b){
 const errors=[]; const need=(ok,message)=>{if(!ok && errors.length<60)errors.push(message);};
 if(!obj(b))return {ok:false,errors:['Report must be a JSON object.']};
 need(b.schema_version==='trialtrace.evidence.v1','Unsupported or missing schema_version.');
 need(text(b.run_id),'Missing run_id.'); need(b.data_kind==='SYNTHETIC','Only labeled synthetic reports are supported.');
 need(b.clinical_validation===false,'clinical_validation must explicitly be false.');
 need(obj(b.producer)&&['CONTRACT_FIXTURE','ARITHMETIC_PROBE','DEMO_ENGINE'].includes(b.producer.kind)&&text(b.producer.version),'Invalid producer identity.');
 need(['PENDING_TEAM_SOURCE_REVIEW','TEAM_REVIEWED_SYNTHETIC_DEMO'].includes(b.review_status),'Invalid review_status.');
 need(obj(b.source)&&typeof b.source.url==='string'&&text(b.source.locator)&&text(b.source.retrieval_status)&&(b.source.pdf_sha256===null||sha(b.source.pdf_sha256)),'Invalid source metadata.');
 need(obj(b.ruleset)&&text(b.ruleset.id)&&text(b.ruleset.version)&&sha(b.ruleset.sha256),'Invalid ruleset metadata.');
 need(Array.isArray(b.limitations)&&b.limitations.length>0&&b.limitations.every(text),'Missing explicit limitations.');
 const files=new Map();
 need(Array.isArray(b.input_files)&&b.input_files.length>0,'Missing input_files.');
 if(Array.isArray(b.input_files))for(const f of b.input_files){
  if(!obj(f)||!text(f.name)||!sha(f.sha256)){need(false,'Invalid input-file metadata.');continue;}
  need(!files.has(f.name),'Duplicate input-file name: '+f.name); files.set(f.name,f.sha256);
 }
 need(Array.isArray(b.findings),'findings must be an array.');
 if(!Array.isArray(b.findings))return {ok:false,errors};
 need(b.findings.length<=10000,'Maximum 10,000 findings.');
 const ids=new Set();
 for(const [i,f] of b.findings.entries()){
  const at='Finding '+(i+1)+': ';
  if(!obj(f)){need(false,at+'must be an object.');continue;}
  need(text(f.finding_id),at+'missing finding_id.');
  need(!ids.has(f.finding_id),at+'duplicate finding_id.');ids.add(f.finding_id);
  need(Number.isInteger(f.record_ordinal)&&f.record_ordinal>0,at+'invalid logical record ordinal.');
  for(const k of ['participant_id','site_id','visit_id','visit_code'])need(f[k]===null||typeof f[k]==='string',at+'invalid/missing '+k+'.');
  need(STATUSES.includes(f.status),at+'unknown status.');need(text(f.reason),at+'missing reason.');
  if(['PASS','POTENTIAL_DEVIATION'].includes(f.status)){
   const c=f.calculation;
   need(obj(c)&&['target','earliest','latest','actual'].every(k=>validDate(c[k]))&&Number.isInteger(c.days_outside)&&c.days_outside>=0,at+'invalid/missing calculation.');
   if(obj(c)){need(f.status==='PASS'?c.days_outside===0:c.days_outside>0,at+'status and days_outside disagree.');}
  }else need(f.calculation===null,at+'unresolved findings require null calculation.');
  need(Array.isArray(f.evidence)&&f.evidence.length>0,at+'missing evidence.');
  if(Array.isArray(f.evidence))for(const e of f.evidence){
   if(!obj(e)){need(false,at+'invalid evidence.');continue;}
   need(text(e.source_file)&&files.has(e.source_file),at+'unknown evidence file.');
   need(sha(e.sha256)&&files.get(e.source_file)===e.sha256,at+'evidence hash does not match declared input metadata.');
   need(Number.isInteger(e.record_ordinal)&&e.record_ordinal>0,at+'invalid evidence ordinal.');
   need(obj(e.raw_record),at+'missing raw evidence object.');
  }
 }
 return {ok:errors.length===0,errors};
}
function summarizeFindings(findings){
 const result={total:findings.length,PASS:0,POTENTIAL_DEVIATION:0,DATA_QUERY:0,NOT_EVALUABLE:0};
 for(const f of findings){if(!STATUSES.includes(f.status))throw Error('Unknown status');result[f.status]++;}
 return result;
}
function filterFindings(findings,status='ALL',query=''){
 const q=query.toLowerCase().trim();
 return findings.filter(f=>(status==='ALL'||f.status===status)&&(!q||['finding_id','participant_id','site_id','visit_id','visit_code','reason'].some(k=>String(f[k]??'').toLowerCase().includes(q))));
}
function safeSourceURL(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}}
const api={STATUSES,validateBundle,summarizeFindings,filterFindings,safeSourceURL};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrialTrace=api;
})(typeof window!=='undefined'?window:globalThis);
