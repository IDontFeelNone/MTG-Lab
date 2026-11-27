"""Entirely original, independently authored MTGJSON-shaped admission evidence."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

from providers.mtgjson.private_policy import (PrivateResearchProfile,SourceUseBasis,
    LIMITED_OPERATIONS,canonical,digest)
from providers.mtgjson.private_import import import_private_release
from query import CanonicalQueryEngine

TIME='2026-11-26T00:00:00Z'
NOTICE=b'Original MTG Lab factual-admission test material. No real card content.\n'
CANARY='INDEPENDENTLY_AUTHORED_EXCLUDED_ABILITY_TEXT_ADMISSION_7b61'


def card_key(n):return f'10000000-0000-4000-8000-{n:012d}'
def print_key(n):return f'20000000-0000-4000-8000-{n:012d}'
def alias_key(n):return f'30000000-0000-4000-8000-{n:012d}'


def row(n,card,name,number):
    return dict(uuid=print_key(n),name=name,number=str(number),layout='normal',
        colors=[],colorIdentity=[],manaCost='{1}',manaValue=1,type='Artifact',language='English',
        rarity='common',finishes=['nonfoil'],identifiers=dict(scryfallOracleId=card_key(card),
        scryfallId=alias_key(n)),text=CANARY,flavorText=CANARY,prices={'fixture':CANARY})


def document():
    first=[row(1,1,'Original Brass Receiver',1),row(3,2,'Original Paper Beacon',2),
           row(4,3,'Original Disputed Plate',3),row(6,4,'Original Folded Dial',4),
           row(7,5,'Original Quiet Spindle',5)]
    second=[row(2,1,'Original Brass Receiver',1),row(5,3,'Original Disputed Plate',2)]
    second[1]['colors']=['U']
    first[3].update(layout='modal_dfc',side='a',faceName='Original Dial Front',otherFaceIds=[])
    return dict(meta=dict(version='5.3.0+authored-admission',date='2026-11-26'),data={
        'FJA':dict(code='FJA',name='Original Fictional Set A',cards=first),
        'FJB':dict(code='FJB',name='Original Fictional Set B',cards=second)})


class Fixture:
    def __init__(self,root,*,source_document=None,baseline=True):
        self.root=Path(root);self.source=self.root/'original.json';self.notice=self.root/'notice.txt'
        self.provenance=self.root/'provenance.json';self.publication=self.root/'factual-publication'
        raw=json.dumps(source_document or document(),separators=(',',':'),ensure_ascii=False).encode();self.source.write_bytes(raw)
        self.notice.write_bytes(NOTICE)
        release=dict(provider='MTGJSON',release_id='original-factual-admission-fixture',
            version='5.3.0+authored-admission',date='2026-11-26',artifact_sha256=digest(raw),
            provenance_reference='original-admission-provenance',notice_reference='original-admission-notice')
        provenance={k:release[k] for k in ('provider','release_id','version','date','artifact_sha256')}
        provenance.update(source_url='urn:mtglab:original:factual-admission',acquired_at=TIME,acquisition_method='MANUALLY_SUPPLIED')
        self.provenance.write_text(canonical(provenance)+'\n')
        basis=SourceUseBasis('original-admission-authorship',digest(NOTICE),'PROJECT_AUTHORSHIP',
            'COMPLETE_ARTIFACT',LIMITED_OPERATIONS,'SUPPORTED')
        self.profile=PrivateResearchProfile.for_release(release,provenance_sha256=digest(self.provenance.read_bytes()),
            notice_sha256=digest(NOTICE),bases=(basis,),internal_decision_reference='original-fixture-only',
            material='ORIGINAL_PROJECT_FIXTURE',retention_mode='limited-retention')
        for p in (self.source,self.notice,self.provenance):p.chmod(0o600)
        self.report=import_private_release(self.source,self.publication,profile=self.profile,
            provenance=self.provenance,notice=self.notice)
        self.receipt=json.loads((self.publication/'output/publication.json').read_bytes())
        self.base=self.root/'baseline';game=self.base/'canonical/games/magic';game.mkdir(parents=True)
        (game/'game.json').write_text(json.dumps(dict(id='magic',name='Magic: The Gathering')))
        state={}
        if baseline:
            state=dict(card={'existing-receiver':dict(entity_type='card',values=dict(name='Original Brass Receiver',
                layout='normal',colors=[],mana_cost='{1}',card_reference=card_key(1)),superseded_status=False)},
                printing={'existing-receiver-print':dict(entity_type='printing',values=dict(uuid=print_key(1),
                card_id='existing-receiver',set_id='fja',collector_number='1',language='en',finish_ids=['nonfoil']),
                superseded_status=False)})
        (self.base/'canonical/state.json').write_text(json.dumps(state))
        self.query=CanonicalQueryEngine('magic',games_root=self.base/'canonical/games',data_root=self.base)

    def assess(self,name='assessment'):
        from canonical_import.mtgjson_factual import assess_factual_publication
        return assess_factual_publication(self.publication,profile=self.profile,
            expected_report_id=self.report['report_id'],expected_publication_id=self.receipt['publication_id'],
            canonical_query=self.query,workspace=self.root/name)
