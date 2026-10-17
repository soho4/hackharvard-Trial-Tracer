import random
from engine import FEATURES

def make_demo():
    r=random.Random(20261016)
    conditions=['Melanoma','Atopic Dermatitis','Non-Small Cell Lung Cancer','Asthma']
    sponsors=['Regeneron Pharmaceuticals','Example BioPharma A','Example BioPharma B','Example Therapeutics C','Example Clinical D']
    out=[]
    for c in conditions:
      for phase in ['PHASE2','PHASE3']:
       for i in range(85):
        year=r.randint(2012,2026); sponsor=r.choices(sponsors,weights=[2,3,2,2,2])[0]
        base=7 if phase=='PHASE2' else 12
        out.append({'nct_id':f'DEMO-{len(out)+1:04d}','title':f'Synthetic {phase} {c} Study {i+1}', 'sponsor':sponsor,'phase':phase,
        'condition':c,'conditions':[c],'study_type':'INTERVENTIONAL','year':year,'enrollment':r.randint(80,650),'status':'COMPLETED',
        'outcomes':max(1,round(r.gauss(base+(year-2012)*0.24+(3 if sponsor==sponsors[0] else 0),4))),
        'criteria':max(3,round(r.gauss(17+(year-2012)*.5,6))),'arms':r.randint(2,4),
        'sites':r.randint(4,45),'countries':r.randint(1,9),'source':'synthetic-demo','eligibility_excerpt':'Synthetic illustrative eligibility criteria.'})
    return out
