import re, statistics, math
from collections import Counter, defaultdict

FEATURES={'outcomes':'Registered outcome measures','criteria':'Estimated eligibility criteria','arms':'Study arms','sites':'Registered locations','countries':'Countries'}

def criteria_count(text):
    if not text: return 0
    lines=[s.strip() for s in text.splitlines() if s.strip()]
    lines=[s for s in lines if not re.match(r'^(inclusion|exclusion) criteria\s*:?$',s,re.I)]
    # estimates bullet/numbered criteria; if unstructured, estimate from sentence breaks
    bullets=[s for s in lines if re.match(r'^(?:[-•*]|\d+[.)])\s+',s)]
    if bullets: return len(bullets)
    return max(1,len([s for s in lines if len(s)>18]))

def normalize(raw):
    p=raw.get('protocolSection',{})
    ids=p.get('identificationModule',{}); d=p.get('designModule',{}); e=p.get('eligibilityModule',{}); status=p.get('statusModule',{})
    loc=p.get('contactsLocationsModule',{}).get('locations',[]) or []
    o=p.get('outcomesModule',{}); ar=p.get('armsInterventionsModule',{}).get('armGroups',[]) or []
    sponsor=p.get('sponsorCollaboratorsModule',{}).get('leadSponsor',{}).get('name','Unknown')
    date=status.get('startDateStruct',{}).get('date','')
    phase=next((x for x in d.get('phases',[]) if x in ('PHASE1','PHASE2','PHASE3','PHASE4')), 'UNKNOWN')
    counts=sum(len(o.get(k,[]) or []) for k in ('primaryOutcomes','secondaryOutcomes','otherOutcomes'))
    return {'nct_id':ids.get('nctId','UNKNOWN'),'title':ids.get('briefTitle','Untitled'), 'sponsor':sponsor,'phase':phase,
      'condition':(p.get('conditionsModule',{}).get('conditions',[]) or ['Unknown'])[0],
      'conditions':p.get('conditionsModule',{}).get('conditions',[]) or [],
      'study_type':d.get('studyType','UNKNOWN'),'year':int(date[:4]) if date[:4].isdigit() else None,
      'enrollment':d.get('enrollmentInfo',{}).get('count'), 'status':status.get('overallStatus','UNKNOWN'),
      'outcomes':counts if any(k in o for k in ('primaryOutcomes','secondaryOutcomes','otherOutcomes')) else None,
      'criteria':criteria_count(e.get('eligibilityCriteria','')) if e.get('eligibilityCriteria','').strip() else None,
      'arms':len(ar) if p.get('armsInterventionsModule',{}).get('armGroups') else None,
      'sites':len(loc) if loc else None,
      'countries':len(set(x.get('country','') for x in loc if x.get('country'))) if any(x.get('country') for x in loc) else None,
      'source':'clinicaltrials.gov','eligibility_excerpt':e.get('eligibilityCriteria','')[:1200]}

def peer_match(target,studies,relax=False):
    peers=[s for s in studies if s['nct_id'] != target['nct_id'] and s.get('study_type') == target.get('study_type') and s.get('phase')==target.get('phase')]
    def similar(a,b):
        aa={x.lower().strip() for x in a.get('conditions',[]) if x};bb={x.lower().strip() for x in b.get('conditions',[]) if x}
        return bool(aa & bb) or (a.get('condition','').lower()==b.get('condition','').lower())
    if not relax: peers=[s for s in peers if similar(target,s) and (not target.get('year') or not s.get('year') or abs(s['year']-target['year'])<=6)]
    return peers

def benchmarks(target,peers):
    data={}
    for key,label in FEATURES.items():
        vals=sorted([s[key] for s in peers if isinstance(s.get(key),(int,float)) and not isinstance(s.get(key),bool)])
        v=target.get(key)
        median=round(statistics.median(vals),1) if vals else None
        valid=isinstance(v,(int,float)) and not isinstance(v,bool)
        pct=round(100*(sum(x<v for x in vals)+.5*sum(x==v for x in vals))/len(vals),1) if valid and vals else None
        data[key]={'name':label,'value':v if valid else None,'median':median,'percentile':pct,
                   'delta':round(v-median,1) if pct is not None else None,'samples':len(vals),
                   'status':'available' if pct is not None else ('missing_study_data' if not valid else 'no_peer_data')}
    return {'study':target,'peer_count':len(peers),'features':data,
      'warning':('Small comparison cohort; interpret percentiles cautiously.' if len(peers)<20 else None),
      'peers':peers, 'peer_records_returned':len(peers),
      'method':'Study type + phase + shared exact condition + start year within 6 years; percentiles use midrank ties. Missing registry values are excluded, not counted as zero. Registry fields are imperfect proxies for protocol complexity.'}

def sponsor_trend(studies,sponsor):
    # Peer-adjusted outcome count within same phase and exact condition, 3-year buckets
    selected=[s for s in studies if sponsor.lower() in s.get('sponsor','').lower() and s.get('year') and isinstance(s.get('outcomes'),int)]
    by_bucket=defaultdict(list)
    for s in selected:
        peers=[p['outcomes'] for p in studies if p.get('phase')==s.get('phase') and p.get('condition','').lower()==s.get('condition','').lower() and isinstance(p.get('outcomes'),int) and p['nct_id']!=s['nct_id']]
        if len(peers)<5: continue
        expected=statistics.median(peers)
        if expected<=0:continue
        yr=2010+3*((s['year']-2010)//3)
        by_bucket[yr].append(s['outcomes']/expected)
    return [{'period':f'{y}–{y+2}','ratio':round(statistics.median(v),2),'n':len(v)} for y,v in sorted(by_bucket.items())]
