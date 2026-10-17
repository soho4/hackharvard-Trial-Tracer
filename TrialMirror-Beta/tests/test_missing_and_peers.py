from engine import normalize, benchmarks
from demo_data import make_demo

def test_unreported_fields_are_missing_not_zero():
    study=normalize({'protocolSection': {'identificationModule': {'nctId':'NCT01866319'},'designModule': {'phases':['PHASE3']}}})
    assert all(study[k] is None for k in ['sites','countries','outcomes','criteria','arms'])

def test_explicit_empty_locations_are_unknown_not_zero():
    study=normalize({'protocolSection': {'contactsLocationsModule': {'locations': []}}})
    assert study['sites'] is None and study['countries'] is None

def test_missing_values_excluded_from_medians():
    t={'nct_id':'TARGET','sites':None,'countries':None,'arms':2}
    peers=[{'nct_id':'A','sites':None,'countries':None,'arms':2},{'nct_id':'B','sites':100,'countries':9,'arms':3}]
    b=benchmarks(t,peers)
    assert b['features']['sites']['value'] is None
    assert b['features']['sites']['percentile'] is None
    assert b['features']['sites']['median']==100
    assert b['features']['sites']['samples']==1
    assert b['features']['arms']['percentile']==25

def test_all_peer_records_present():
    target=make_demo()[0]
    peers=make_demo()[1:90]
    b=benchmarks(target, peers)
    assert len(b['peers'])==89
    assert b['peers'][0]['title'] and b['peers'][0]['sponsor']
