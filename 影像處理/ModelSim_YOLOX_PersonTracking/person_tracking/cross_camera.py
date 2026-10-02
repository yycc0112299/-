"""Hand-written conservative cross-camera appearance association, no ReID model."""
import numpy as np

def appearance_similarity(first,second):
    """Soft color overlap; upper clothing remains useful in partial-body views."""
    region_overlap=np.minimum(first,second).sum(axis=1)
    return float(.75*region_overlap[0]+.25*region_overlap[1])

class CrossCameraMatcher:
    def __init__(self,threshold=.72,margin=.08,min_hits=3):
        self.threshold=threshold;self.margin=margin;self.min_hits=min_hits
        self.streaks={};self.labels={};self.next_label=1

    def update(self,a,b,excluded_pairs=None):
        # Only actual, confirmed observations can establish a cross-camera pair.
        a=[d for d in a if d['status']=='confirmed']
        b=[d for d in b if d['status']=='confirmed']
        excluded_pairs=excluded_pairs or set()
        scores=np.zeros((len(a),len(b)))
        for i,x in enumerate(a):
            for j,y in enumerate(b):
                scores[i,j]=(-1 if (x['track_id'],y['track_id']) in excluded_pairs
                             else appearance_similarity(x['appearance'],y['appearance']))
        accepted={};pairs=[]
        for i,x in enumerate(a):
            if not b:continue
            j=int(scores[i].argmax());score=float(scores[i,j])
            if score<0:continue
            row=sorted(scores[i],reverse=True);col=sorted(scores[:,j],reverse=True)
            ambiguous=(len(row)>1 and score-row[1]<self.margin) or (len(col)>1 and score-col[1]<self.margin)
            if score<self.threshold:status='unmatched'
            elif int(scores[:,j].argmax())!=i or ambiguous:status='ambiguous'
            else:
                key=(x['track_id'],b[j]['track_id']);hits=self.streaks.get(key,0)+1
                accepted[key]=hits
                status='confirmed_candidate' if hits>=self.min_hits else 'candidate'
                if hits>=self.min_hits and key not in self.labels:
                    self.labels[key]=self.next_label;self.next_label+=1
            key=(x['track_id'],b[j]['track_id'])
            pairs.append(dict(a_id=key[0],b_id=key[1],score=round(score,4),status=status,
                consecutive_hits=accepted.get(key,0),
                pair_label=f'P{self.labels[key]}' if status=='confirmed_candidate' else None))
        # Missing/ambiguous observations break confirmation; old labels do not force matches.
        self.streaks=accepted
        return pairs
