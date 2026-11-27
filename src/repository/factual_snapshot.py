"""Bounded private factual profile in the existing canonical snapshot architecture.

Publication is a new immutable generation, never an in-place default catalog
replacement. The existing admission capability, promotion, typed projection and
repository transaction own their respective gates. No provider input is parsed.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path
from jsonschema import Draft202012Validator

from acquisition.knowledge import ProviderPolicy, build_review_package
from acquisition.promotion import CanonicalPromotionEngine, PromotionDecision
from projection.engine import TypedCanonicalProjectionEngine
from production_evidence.automatic_updates import (AdmissionDecision, AdmissionReviewBoundary,
    IsolatedAdmissionTestBoundary, ADMISSION_OPERATION)
from repository.snapshots import SnapshotVerification, SnapshotError, _read_tree, _relative
from canonical_import.mtgjson_factual import (FactualAssessment, FactualAdmissionError, require,
    stable, identity, file_hash, private_root, write_once, prepare_cohort, engine_binding,validate_cohort_manifest)

PROFILE = 'private-factual-canonical-snapshot-v1'
_SEAL = object()
CAPABILITIES = dict(catalog_query_collection='available',factual_inspection='available',
    mechanical_semantics='unsupported',rules_execution='unsupported',format_legality='unsupported',
    public_export='unsupported',external_ai_export='unsupported')


def _sync(root):
    for path in sorted(root.rglob('*')):
        if path.is_file():
            with path.open('rb') as stream:os.fsync(stream.fileno())
    for path in [*sorted((p for p in root.rglob('*') if p.is_dir()),reverse=True),root]:
        descriptor=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)


def _sync_parent(path):
    descriptor=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def _bindings(manifest, root):
    return dict(operation=ADMISSION_OPERATION,repository_root=str(root),
        manifest_id=manifest['manifest_id'],canonical_pre_state_digest=manifest['canonical_pre_state'],
        source=deepcopy(manifest['source']),policy=manifest['policy'],implementation=manifest['implementation'],
        candidate_ids=[[x['entity_type'],x['record']['id']] for x in manifest['documents']],
        dependency_closure=manifest['dependency_closure'],capabilities=manifest['capabilities'])


def _authorize(boundary, bindings):
    require(boundary is not None and callable(getattr(boundary,'authorize',None))
        and type(getattr(boundary,'authenticated_reviewer',None)) is str,
        'authenticated admission boundary required','UNAUTHENTICATED')
    try:decision=boundary.authorize(deepcopy(bindings))
    except (ValueError,OSError,TypeError,RuntimeError):
        raise FactualAdmissionError('UNAUTHENTICATED','trusted admission review unavailable or refused') from None
    require(type(decision) is AdmissionDecision and decision.decision=='approved'
        and decision.operation==ADMISSION_OPERATION and decision.bindings==bindings
        and decision.reviewer==boundary.authenticated_reviewer and decision.reviewer.strip()
        and type(decision.review_reference) is str and decision.review_reference
        and type(decision.decided_at) is str and decision.decided_at,
        'exact authenticated admission decision required','UNAUTHENTICATED')
    from datetime import datetime
    try:
        require(datetime.fromisoformat(decision.decided_at.replace('Z','+00:00')).utcoffset() is not None,
            'review timestamp must have a timezone','UNAUTHENTICATED')
    except (ValueError,TypeError):
        raise FactualAdmissionError('UNAUTHENTICATED','invalid admission review time') from None
    if isinstance(boundary,IsolatedAdmissionTestBoundary):
        require(decision.scope=='isolated-test','isolated authority cannot approve production','UNAUTHENTICATED')
        boundary._verify_root(Path(bindings['repository_root']))
    else:
        require(decision.scope=='production' and not decision.review_reference.startswith('SIMULATED'),
            'production host authority required','UNAUTHENTICATED')
    return decision


def _package(manifest):
    """Map verified derivative lineage into the existing review package, honestly.

    This is not a new acquisition. The retained source hash is a lineage identity;
    no archive is opened and no source timestamp is fabricated.
    """
    source=manifest['source'];release=source['release'];assertions=manifest['assertions']
    provider=assertions[0]['source_id']
    policy=ProviderPolicy(provider,'derived',1.0,('private-only','no-ai-export','no-oracle'),
        'MTGJSON factual derivative; verified correspondence, not calibrated truth confidence',('card','printing'))
    run=dict(schema_version='acquisition-run-v1',provider_id=provider,
        run_id='factual-publication-read-'+source['report_id'][7:],status='VERIFIED_DERIVATIVE_READ_NOT_NEW_ACQUISITION',
        factual_publication_id=source['publication_id'],source_profile_id=source['profile_id'])
    snapshot=dict(schema_version='raw-snapshot-v1',provider_id=provider,
        snapshot_id=release['artifact_sha256'],checksum={'value':release['artifact_sha256']},
        dataset=release['release_id'],publication_timestamp=release['date']+'T00:00:00Z')
    normalized=dict(schema_version='normalized-source-record-v1',provider_id=provider,
        raw_snapshot_id=release['artifact_sha256'],records=[])
    for document in manifest['documents']:
        cid=document['record']['id']
        normalized['records'].append(dict(schema_version='normalized-source-record-v1',id=cid,
            raw_snapshot_id=release['artifact_sha256'],source_record_id=cid,
            source_values={a['path'].lstrip('/'):a['asserted_value'] for a in assertions if a['subject_id']==cid},
            unmapped_source_fields={},validation_errors=[]))
    # Existing review-package validation requires an explicit raw lineage note.
    owned=deepcopy(assertions)
    for assertion in owned:
        assertion['notes']+='; raw_snapshot_id='+release['artifact_sha256']
    package=build_review_package(run,[snapshot],[normalized],owned,policy,release['version'])
    return package,policy


def verify_factual_snapshot(root, *, expected_snapshot_id, expected_manifest_id):
    """Verify an exact immutable generation. Integrity alone grants no attachment."""
    root=private_root(root)
    files=_read_tree(root)
    require('publication.json' in files,'snapshot publication marker missing','INCOMPLETE_PUBLICATION')
    try:
        receipt=json.loads(files['publication.json'])
        schema=json.loads((Path(__file__).parents[1]/'schemas/v1/private-factual-canonical-snapshot.schema.json').read_bytes())
        require(Draft202012Validator(schema).is_valid(receipt),'invalid factual snapshot contract','INTEGRITY_MISMATCH')
        body={k:v for k,v in receipt.items() if k!='snapshot_id'}
        require(receipt['snapshot_id']==expected_snapshot_id==identity(body),'snapshot identity mismatch','INTEGRITY_MISMATCH')
        require(receipt['profile']==PROFILE and receipt['manifest_id']==expected_manifest_id
            and receipt['capabilities']==CAPABILITIES,'snapshot scope mismatch','INTEGRITY_MISMATCH')
        require(set(files)==set(receipt['files'])|{'publication.json'},'snapshot inventory changed','INTEGRITY_MISMATCH')
        for name,pin in receipt['files'].items():
            require(len(files[name])==pin['bytes'] and hashlib.sha256(files[name]).hexdigest()==pin['sha256'],
                'snapshot file changed','INTEGRITY_MISMATCH')
            require((root/name).stat().st_mode & 0o077 == 0,'private snapshot access changed','PRIVATE_BOUNDARY')
        manifest=json.loads(files['cohort.json'])
        validate_cohort_manifest(manifest)
        require(identity({k:v for k,v in manifest.items() if k!='manifest_id'})==expected_manifest_id
            and manifest['implementation']==engine_binding(),'cohort or compatible engine changed','INCOMPATIBLE_ENGINE')
        require(receipt['source']==manifest['source'] and receipt['canonical_pre_state']==manifest['canonical_pre_state'],
            'snapshot lineage mismatch','INTEGRITY_MISMATCH')
        admission=json.loads(files['admission.json'])
        require(admission['manifest_id']==expected_manifest_id and admission['decision']['decision']=='approved'
            and admission['decision']['bindings']==_bindings(manifest,Path(admission['operator_root']))
            and admission['decision']['scope']==receipt['authorization_scope'],
            'retained admission evidence mismatch','INTEGRITY_MISMATCH')
        # Validate the exact existing typed repository, including all field sources.
        from repository.canonical import CanonicalRepository
        catalog=CanonicalRepository('magic',games_root=root/'data/canonical/games')
        expected={(x['entity_type'],x['record']['id']):x['record'] for x in manifest['documents']}
        require(len(catalog.cards)+len(catalog.printings)==len(expected),'snapshot population mismatch','INTEGRITY_MISMATCH')
        by_subject={}
        for assertion in manifest['assertions']:
            projected=deepcopy(assertion)
            projected.pop('schema_version')
            projected['status']='promoted'
            projected['notes']+='; raw_snapshot_id='+manifest['source']['release']['artifact_sha256']
            by_subject.setdefault(assertion['subject_id'],[]).append(projected)
        for (kind,cid),record in expected.items():
            relative=f'data/canonical/games/magic/{kind}s/{cid}/{kind}.json'
            actual=json.loads(files[relative])
            require({k:v for k,v in actual.items() if k not in ('metadata','assertions')}==
                {k:v for k,v in record.items() if k not in ('metadata','assertions')},'typed factual values mismatch','INTEGRITY_MISMATCH')
            assertions=actual['assertions']
            require(sorted(assertions,key=lambda a:a['id'])==sorted(by_subject[cid],key=lambda a:a['id'])
                and actual['metadata']['source_assertion_ids']==sorted(a['id'] for a in by_subject[cid]),
                'typed assertion provenance correspondence mismatch','INTEGRITY_MISMATCH')
    except FactualAdmissionError:
        raise
    except (ValueError,OSError,KeyError,TypeError):
        raise FactualAdmissionError('INTEGRITY_MISMATCH','private factual snapshot verification refused') from None
    return receipt


@dataclass(frozen=True)
class FactualPublication:
    root: Path
    _receipt: str
    _boundary: object
    _operator_root: Path
    _seal: object

    @property
    def receipt(self):return json.loads(self._receipt)


def admit_factual_cohort(assessment, manifest, operator_root, *, expected_manifest_id,
                        review_boundary: AdmissionReviewBoundary, expected_existing_snapshot_id=None):
    """Authenticate, construct with existing engines, durably publish one generation.

    No live default is changed. Failed generations remain isolated for inspection;
    a subsequent attempt refuses pending recovery rather than deleting evidence.
    """
    require(type(assessment) is FactualAssessment,'live verified factual assessment required','UNTRUSTED_INPUT')
    assessment.verify()
    require(type(manifest) is dict and manifest.get('manifest_id')==expected_manifest_id,
        'independent cohort pin required','INTEGRITY_MISMATCH')
    fresh=prepare_cohort(assessment,manifest.get('selected_card_ids'),expected_assessment_id=assessment.report['assessment_id'])
    validate_cohort_manifest(fresh)
    require(stable(manifest)==stable(fresh),'cohort changed or stale','INTEGRITY_MISMATCH')
    root=private_root(operator_root)
    bindings=_bindings(fresh,root)
    decision=_authorize(review_boundary,bindings)
    assessment.verify()  # A callback is never allowed to change the reviewed inputs.
    require(prepare_cohort(assessment,fresh['selected_card_ids'],expected_assessment_id=fresh['assessment_id'])==fresh,
        'cohort changed during review','INTEGRITY_MISMATCH')
    snapshots=private_root(root/'snapshots',create=True)
    destination=snapshots/expected_manifest_id[7:]
    staging=root/'.factual-admission-staging'
    require(not staging.exists(),'admission recovery required; preserve staging','RECOVERY_REQUIRED')
    if destination.exists():
        require(expected_existing_snapshot_id is not None,
            'independently retained snapshot pin required for existing generation','INDEPENDENT_PIN_REQUIRED')
        receipt=verify_factual_snapshot(destination,expected_snapshot_id=expected_existing_snapshot_id,expected_manifest_id=expected_manifest_id)
        require(decision.scope==receipt['authorization_scope'],
            'existing generation authority scope cannot be substituted','UNAUTHENTICATED')
        _sync(destination);_sync_parent(snapshots);_sync_parent(root)
        return FactualPublication(destination,stable(receipt),review_boundary,root,_SEAL)
    try:staging.mkdir(mode=0o700)
    except FileExistsError:
        raise FactualAdmissionError('RECOVERY_REQUIRED','admission workspace already owned; preserve staging') from None
    verified_snapshot_id=None
    try:
        _sync_parent(root)  # Persist new snapshots/staging directory entries.
        game=staging/'data/canonical/games/magic';game.mkdir(parents=True,mode=0o700)
        write_once(game/'game.json',dict(id='magic',name='Magic: The Gathering'))
        write_once(staging/'cohort.json',fresh)
        write_once(staging/'admission.json',dict(manifest_id=expected_manifest_id,operator_root=str(root),
            decision=decision.as_dict(),authority='LIVE_HOST_AUTHENTICATION_AT_PUBLICATION_NOT_JSON_SELF_APPROVAL'))
        package,policy=_package(fresh)
        promoter=CanonicalPromotionEngine(staging/'data/canonical',staging/'data/audit')
        promoter.promote(package,policy,PromotionDecision(decision.reviewer,decision.decided_at,
            reason='authenticated exact factual cohort '+expected_manifest_id))
        projection=TypedCanonicalProjectionEngine(staging/'data/canonical',staging/'data/canonical/games',
            staging/'data/projection-audit')
        projected=projection.project(decision.decided_at)
        # The existing transaction does prospective/relationship validation.
        require(projected['validation_result']['valid'],'existing typed projection refused')
        for p in staging.rglob('*'):
            p.chmod(0o700 if p.is_dir() else 0o600)
        files={p.relative_to(staging).as_posix():dict(bytes=p.stat().st_size,sha256=file_hash(p))
            for p in sorted(staging.rglob('*')) if p.is_file()}
        body=dict(schema_version='v1',profile=PROFILE,game='magic',manifest_id=expected_manifest_id,
            canonical_pre_state=fresh['canonical_pre_state'],source=fresh['source'],files=files,
            capabilities=CAPABILITIES,canonical_authority='SELECTED_REVIEWED_FACTUAL_COHORT_ONLY',
            authorization_scope=decision.scope,semantic_authority='NOT_ESTABLISHED',real_card_execution='BLOCKED',default_catalog_changed=False)
        receipt=dict(body,snapshot_id=identity(body))
        write_once(staging/'publication.json',receipt)
        verify_factual_snapshot(staging,expected_snapshot_id=receipt['snapshot_id'],expected_manifest_id=expected_manifest_id)
        verified_snapshot_id=receipt['snapshot_id']
        assessment.verify()
        # Reauthenticate the exact operation immediately before durable publication.
        _authorize(review_boundary,bindings)
        assessment.verify()
        _sync(staging)
        assessment.verify()
        os.rename(staging,destination)
        _sync_parent(snapshots)
        _sync_parent(root)
        verify_factual_snapshot(destination,expected_snapshot_id=receipt['snapshot_id'],expected_manifest_id=expected_manifest_id)
        return FactualPublication(destination,stable(receipt),review_boundary,root,_SEAL)
    except FactualAdmissionError as error:
        if verified_snapshot_id is not None:error.verified_snapshot_id=verified_snapshot_id
        raise
    except (ValueError,OSError,KeyError,TypeError,RuntimeError):
        error=FactualAdmissionError('PUBLICATION_FAILED','private admission failed; preserve generation/staging for recovery')
        if verified_snapshot_id is not None:error.verified_snapshot_id=verified_snapshot_id
        raise error from None


@dataclass(frozen=True)
class FactualSnapshotAttachment(SnapshotVerification):
    _publication: FactualPublication

    @property
    def data_root(self):return self.root/'data'

    @property
    def games_root(self):return self.data_root/'canonical/games'

    def require_capability(self,name):
        if name not in ('catalog_query_collection','factual_inspection'):
            raise SnapshotError('capability is outside the factual profile',code='unsupported_capability')

    def verify_unchanged(self):
        publication=self._publication
        require(type(publication) is FactualPublication and publication._seal is _SEAL,
            'live authenticated factual publication required','UNAUTHENTICATED')
        receipt=publication.receipt
        require(publication.root==self.root and stable(receipt).encode()==self._metadata,
            'factual attachment scope changed','INTEGRITY_MISMATCH')
        manifest=self.read_json(self.root/'cohort.json')
        live=_authorize(publication._boundary,_bindings(manifest,publication._operator_root))
        require(live.scope==receipt['authorization_scope'],'admission scope substitution refused','UNAUTHENTICATED')
        current=verify_factual_snapshot(self.root,expected_snapshot_id=receipt['snapshot_id'],expected_manifest_id=receipt['manifest_id'])
        require(current==receipt,'factual attachment changed','INTEGRITY_MISMATCH')

    def _name(self,path):
        try:name=Path(path).relative_to(self.root).as_posix()
        except ValueError:raise SnapshotError('read outside selected factual snapshot',code='scope_mismatch') from None
        _relative(name)
        return name

    def paths(self,root,pattern):
        base=self._name(root);pattern=base+'/'+pattern
        from repository.legacy_profile import _matches
        return tuple(self.root/name for name in sorted(self.binding['files']) if _matches(name,pattern))

    def read_bytes(self,path):
        self.require(path)
        name=self._name(path);pin=self.binding['files'].get(name)
        require(pin is not None,'unselected factual dependency','PRIVATE_BOUNDARY')
        require(Path(path).is_file() and not Path(path).is_symlink() and Path(path).stat().st_size==pin['bytes'],
            'factual dependency changed','INTEGRITY_MISMATCH')
        with Path(path).open('rb') as stream:raw=stream.read(pin['bytes']+1)
        require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
            'factual dependency changed during read','INTEGRITY_MISMATCH')
        return raw

    def require(self,path):
        require(self._name(path) in self.binding['files'],'unselected factual dependency','PRIVATE_BOUNDARY')

    def read_json(self,path):return json.loads(self.read_bytes(path))

    def validate_query(self,snapshot):
        manifest=self.read_json(self.root/'cohort.json')
        expected={(x['entity_type'],x['record']['id']) for x in manifest['documents']}|{('game','magic')}
        require(snapshot.game=='magic' and {(x.entity_type,x.canonical_identity) for x in snapshot.entities}==expected,
            'query population differs from admitted cohort','INTEGRITY_MISMATCH')


def attach_factual_snapshot(publication, *, expected_snapshot_id):
    """Explicitly select an authenticated publication, never a serialized approval."""
    require(type(publication) is FactualPublication and publication._seal is _SEAL,
        'live authenticated publication required','UNAUTHENTICATED')
    receipt=publication.receipt
    require(expected_snapshot_id==receipt['snapshot_id'],'independent snapshot pin mismatch','INTEGRITY_MISMATCH')
    result=FactualSnapshotAttachment(publication.root,stable(receipt).encode(),publication)
    result.verify_unchanged()
    return result


def reopen_factual_snapshot(root, *, expected_snapshot_id, expected_manifest_id, review_boundary):
    """Reopen after restart only with independent pins and a live trusted host."""
    receipt=verify_factual_snapshot(root,expected_snapshot_id=expected_snapshot_id,expected_manifest_id=expected_manifest_id)
    retained=json.loads((Path(root)/'admission.json').read_bytes())
    manifest=json.loads((Path(root)/'cohort.json').read_bytes())
    operator=private_root(retained['operator_root'])
    require(Path(root).absolute()==operator/'snapshots'/expected_manifest_id[7:],
        'snapshot operator scope mismatch','PRIVATE_BOUNDARY')
    live=_authorize(review_boundary,_bindings(manifest,operator))
    require(live.scope==receipt['authorization_scope'],'test authority cannot become production admission','UNAUTHENTICATED')
    publication=FactualPublication(Path(root).absolute(),stable(receipt),review_boundary,operator,_SEAL)
    _sync(Path(root));_sync_parent(Path(root).parent);_sync_parent(operator)
    return attach_factual_snapshot(publication,expected_snapshot_id=expected_snapshot_id)
