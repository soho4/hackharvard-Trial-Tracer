"""Transparent operational scenario enumeration. NOT clinical protocol optimization."""
from pydantic import BaseModel, Field
from typing import Literal

class Scenario(BaseModel):
    patients: int = Field(500, ge=50, le=5000)
    sites: int = Field(20, ge=1, le=200)
    visits: int = Field(12, ge=1, le=60)
    screen_failure_pct: float = Field(35, ge=0, le=95)
    screened_per_site_month: float = Field(4, gt=0, le=100)
    visit_cost_usd: float = Field(180, ge=0, le=100000)
    site_setup_usd: float = Field(35000, ge=0, le=1000000)
    monthly_overhead_usd: float = Field(40000, ge=0, le=10000000)
    priority: Literal['balanced','cost','speed','burden'] = 'balanced'
    min_visits: int = Field(8, ge=1, le=60)
    max_sites: int = Field(40, ge=1, le=200)
    lock_visits: bool = True
    lock_sites: bool = False

def metrics(s, visits, sites):
    import math
    attempts=s.patients/(1-s.screen_failure_pct/100)
    months=3+attempts/(sites*s.screened_per_site_month)
    return {'visits':visits,'sites':sites,'screening_attempts':math.ceil(attempts),'months':round(months,2), 'participant_visits':visits*s.patients,
            'cost_usd':round(s.patients*visits*s.visit_cost_usd+sites*s.site_setup_usd+months*s.monthly_overhead_usd,2)}

def optimize(s):
    if s.min_visits>s.visits: raise ValueError('Minimum visits cannot exceed baseline visits')
    if s.max_sites<s.sites: raise ValueError('Maximum sites cannot be less than baseline sites')
    baseline=metrics(s,s.visits,s.sites)
    vs=[s.visits] if s.lock_visits else list(range(s.min_visits,s.visits+1))
    ss=[s.sites] if s.lock_sites else list(range(s.sites,s.max_sites+1, max(1,(s.max_sites-s.sites)//12 or 1)))
    if not s.lock_sites and ss[-1]!=s.max_sites:ss.append(s.max_sites)
    candidates=[metrics(s,v,site) for v in vs for site in ss]
    def dominates(a,b):
        keys=['cost_usd','months','participant_visits']
        return all(a[k]<=b[k] for k in keys) and any(a[k]<b[k] for k in keys)
    frontier=[x for x in candidates if not any(dominates(y,x) for y in candidates)]
    def score(x):
        if s.priority=='cost':return x['cost_usd']
        if s.priority=='speed':return x['months']
        if s.priority=='burden':return x['participant_visits'],x['cost_usd']
        return x['cost_usd']/max(1,baseline['cost_usd'])+x['months']/max(1,baseline['months'])+x['participant_visits']/max(1,baseline['participant_visits'])
    ranked=sorted(frontier,key=lambda x:(score(x),x['cost_usd']))
    return {'baseline':baseline,'recommended':ranked[0],'frontier':ranked[:35], 'evaluated':len(candidates), 'assumptions':{'site_startup_months':3,'screening_capacity_constant':True,'site_setup_one_time':True,'independent_screening_success':True},'warning':'Illustrative operations model only. Visit reduction is disabled by default; unlock only after qualified clinical review. No medical efficacy, statistical power, or regulatory acceptability is modeled.'}
