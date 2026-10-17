from optimizer import Scenario, optimize
from fastapi.testclient import TestClient
from main import app

def test_locked_visits_not_removed():
    r=optimize(Scenario())
    assert r['recommended']['visits']==12
    assert all(x['visits']==12 for x in r['frontier'])

def test_zero_change_when_all_locked():
    r=optimize(Scenario(lock_sites=True,lock_visits=True))
    assert r['baseline']==r['recommended']

def test_more_sites_reduces_screening_duration():
    from optimizer import metrics
    s=Scenario()
    assert metrics(s,12,30)['months']<metrics(s,12,20)['months']

def test_optim_api():
    c=TestClient(app)
    r=c.post('/api/optimizer/run',json=Scenario().model_dump())
    assert r.status_code==200
    assert r.json()['evaluated']>1

def test_bad_limits():
    c=TestClient(app)
    r=c.post('/api/optimizer/run',json=Scenario(max_sites=1).model_dump())
    assert r.status_code==422
