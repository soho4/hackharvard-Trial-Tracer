import os, re, time
from pathlib import Path
from urllib.parse import quote
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from engine import normalize, peer_match, benchmarks, sponsor_trend
from demo_data import make_demo
from optimizer import Scenario, optimize
from pydantic import ValidationError

ROOT=Path(__file__).resolve().parent
API='https://clinicaltrials.gov/api/v2'
app=FastAPI(title='TrialMirror Design Studio',version='0.4.0')
app.mount('/static',StaticFiles(directory=str(ROOT/'static')),name='static')
DEMO=make_demo()
CACHE={}

def fetch(path, params=None):
    try:
        with httpx.Client(timeout=18,headers={'User-Agent':'TrialMirror-HackHarvard-Beta/0.2'}) as c:
            resp=c.get(API+path,params=params)
            resp.raise_for_status()
            data=resp.json()
            if not isinstance(data,dict): raise ValueError('Registry returned unexpected JSON structure')
            return data
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code==404: raise HTTPException(404,'Study not found in ClinicalTrials.gov')
        raise HTTPException(503,'Registry returned HTTP '+str(exc.response.status_code))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'ClinicalTrials.gov unavailable: {str(exc)[:180]}. Use offline demo instead.')

def live_study(nct):
    nct=nct.upper().strip()
    if not re.fullmatch(r'NCT\d{8}',nct): raise HTTPException(400,'Enter a valid NCT identifier, e.g. NCT01234567')
    data=fetch('/studies/'+nct)
    found=data.get('protocolSection',{}).get('identificationModule',{}).get('nctId','')
    if found.upper()!=nct: raise HTTPException(502,'Registry returned a record with a mismatching NCT identifier')
    return normalize(data)

@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')

@app.get('/api/health')
def health():return {'ok':True,'version':'0.4.0','demo_records':len(DEMO)}

@app.get('/api/demo/studies')
def demo_studies():return {'mode':'synthetic-demo','studies':DEMO[:80],'count':len(DEMO),'sponsors':sorted(set(x['sponsor'] for x in DEMO))}

@app.get('/api/demo/benchmark/{nct}')
def demo_benchmark(nct:str):
    target=next((s for s in DEMO if s['nct_id']==nct),None)
    if target is None:raise HTTPException(404,'Synthetic study not found')
    peers=peer_match(target,DEMO)
    return {'mode':'synthetic-demo',**benchmarks(target,peers)}

@app.get('/api/demo/trends')
def demo_trends(sponsor:str='Regeneron Pharmaceuticals'):
    return {'mode':'synthetic-demo','sponsor':sponsor,'trends':sponsor_trend(DEMO,sponsor)}

@app.get('/api/live/study/{nct}')
def live_study_endpoint(nct:str):return {'mode':'live-registry','study':live_study(nct)}

@app.get('/api/live/benchmark/{nct}')
def live_benchmark(nct:str, max_records:int=Query(500,ge=50,le=1000)):
    study=live_study(nct)
    if not study.get('condition') or study['condition']=='Unknown':raise HTTPException(422,'No condition available to form a peer cohort')
    query={'query.cond':study['condition'],'pageSize':min(max_records,100),'format':'json','countTotal':'true'}
    raw=[]; token=None; registry_total=None
    for idx in range((max_records+99)//100):
        params=dict(query)
        if token:params['pageToken']=token
        chunk=fetch('/studies',params)
        if registry_total is None: registry_total=chunk.get('totalCount')
        raw+=chunk.get('studies',[])
        token=chunk.get('nextPageToken')
        if not token or len(raw)>=max_records:break
    studies=[]
    for obj in raw[:max_records]:
        try:studies.append(normalize(obj))
        except (KeyError,ValueError,TypeError):continue
    peers=peer_match(study,studies)
    result=benchmarks(study,peers)
    return {'mode':'live-registry','candidate_count':len(studies),'registry_total':registry_total,
      'coverage_note':'Peers were selected from a capped API sample, not necessarily the entire eligible registry. Results can be sensitive to API ordering.','peer_selection':'strict',**result}

@app.post('/api/optimizer/run')
def optimizer_run(scenario: Scenario):
    try:return optimize(scenario)
    except ValueError as e:raise HTTPException(422,str(e))

@app.get('/api/live/verify/{nct}')
def verify_registry_record(nct:str):
    study=live_study(nct)
    return {'mode':'live-registry','study':study,'source_url':f'https://clinicaltrials.gov/study/{study["nct_id"]}', 'verified_nct':study['nct_id']==nct.upper(),'fields':['protocolSection.identificationModule','protocolSection.designModule','protocolSection.outcomesModule','protocolSection.eligibilityModule','protocolSection.contactsLocationsModule'], 'note':'Derived counts are displayed separately from original registry data. Values may be missing or approximate.'}
