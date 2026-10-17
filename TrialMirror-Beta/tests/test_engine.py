from engine import criteria_count, normalize, peer_match, benchmarks, sponsor_trend
from demo_data import make_demo

def test_demo_data():
    rows=make_demo()
    assert len(rows)==680
    assert all(s['nct_id'].startswith('DEMO-') for s in rows)

def test_peers():
    rows=make_demo();target=rows[0]
    peers=peer_match(target,rows)
    assert peers and all(p['phase']==target['phase'] and p['condition']==target['condition'] and abs(p['year']-target['year'])<=6 for p in peers)
    assert target not in peers

def test_benchmark_range():
    rows=make_demo(); b=benchmarks(rows[0],peer_match(rows[0],rows))
    assert b['peer_count']>0
    assert all(0<=x['percentile']<=100 for x in b['features'].values())

def test_ties_midrank():
    target={'nct_id':'A','outcomes':3}; peers=[{'nct_id':str(i),'outcomes':3} for i in range(4)]
    assert benchmarks(target,peers)['features']['outcomes']['percentile']==50

def test_criteria():
    assert criteria_count('Inclusion Criteria:\n- Adult\n- Signed consent\nExclusion Criteria:\n- Pregnant')==3

def test_trends():
    assert len(sponsor_trend(make_demo(),'Regeneron'))>1
