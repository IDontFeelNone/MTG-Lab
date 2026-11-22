"""Trusted-host, operation-scoped private research policy; never a data license.

Profiles are constructed by host code after reviewing the referenced evidence.
No profile is loaded from source JSON and no real-source profile ships enabled.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re

RETENTION = 'private-factual-v1'
OPERATIONS = ('WHOLE_ARTIFACT_READ', 'LOCAL_PARSE', 'TEMPORARY_MIXED_PROCESSING',
              'PRIVATE_SOURCE_RETENTION', 'PRIVATE_FACTUAL_RETENTION', 'PRIVATE_REPORTS')
FACTUAL_FIELDS = frozenset(('uuid', 'name', 'number', 'layout', 'colors', 'colorIdentity',
    'manaCost', 'manaValue', 'power', 'toughness', 'loyalty', 'defense', 'type', 'types',
    'subtypes', 'supertypes', 'language', 'rarity', 'finishes', 'side', 'faceName', 'otherFaceIds'))
IDENTIFIERS = frozenset(('scryfallOracleId', 'oracleId', 'scryfallId'))
SET_FIELDS = frozenset(('code', 'name', 'releaseDate'))


class SourcePolicyError(ValueError):
    code = 'SOURCE_POLICY_REFUSAL'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False)


def digest(value):
    return hashlib.sha256(value if type(value) is bytes else canonical(value).encode()).hexdigest()


def _check(condition, message):
    if not condition:
        raise SourcePolicyError(message)


def _reference(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:._-]{0,255}', value)


def _sha(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value)


@dataclass(frozen=True)
class SourceUseBasis:
    """Independently reviewed evidence, supplied by the trusted host, not the dataset.

    A digest binds evidence; it does not authenticate its issuer or establish law.
    PUBLISHER_PERMISSION covers only material within the reviewed grant's scope.
    INTERNAL_POLICY records risk posture and cannot supply external rights.
    """
    reference: str
    sha256: str
    kind: str
    material_scope: str
    operations: tuple[str, ...]
    disposition: str

    def validate(self):
        _check(_reference(self.reference) and _sha(self.sha256), 'bound evidence reference required')
        _check(self.kind in ('PROJECT_AUTHORSHIP', 'PUBLISHER_PERMISSION',
                            'QUALIFIED_DETERMINATION', 'INTERNAL_POLICY'), 'unsupported basis kind')
        _check(self.material_scope in ('COMPLETE_ARTIFACT', 'FACTUAL_PROJECTION',
                                      'PUBLISHER_CONTROLLED_ONLY'), 'explicit material scope required')
        _check(type(self.operations) is tuple and all(type(x) is str for x in self.operations)
               and len(set(self.operations)) == len(self.operations)
               and all(x in OPERATIONS for x in self.operations), 'invalid operation scope')
        _check(self.disposition in ('SUPPORTED', 'NOT_ESTABLISHED', 'EXPRESSLY_RESTRICTED'),
               'explicit evidence disposition required')


@dataclass(frozen=True)
class PrivateResearchProfile:
    """Exact-release host disposition. No boolean private-use or owner-approval bypass.

    The host must independently verify the evidence and its scope before creation.
    This object is not an authentication service or an external license.
    """
    release_json: str
    provenance_sha256: str
    notice_sha256: str
    bases: tuple[SourceUseBasis, ...]
    internal_decision_reference: str
    material: str

    @classmethod
    def for_release(cls, release, *, provenance_sha256, notice_sha256, bases,
                    internal_decision_reference, material):
        _check(type(release) is dict and set(release) == {'provider', 'release_id', 'version',
            'date', 'artifact_sha256', 'provenance_reference', 'notice_reference'}, 'closed release required')
        _check(release['provider'] == 'MTGJSON' and _sha(release['artifact_sha256'])
               and all(type(v) is str and 0 < len(v) <= 256 for v in release.values()), 'invalid release')
        result = cls(canonical(release), provenance_sha256, notice_sha256, bases,
                     internal_decision_reference, material)
        result.validate()
        return result

    def validate(self):
        _check(type(self.release_json) is str and len(self.release_json) <= 4096, 'bounded release binding required')
        try:
            release = json.loads(self.release_json)
        except (ValueError, TypeError):
            raise SourcePolicyError('invalid release binding') from None
        _check(type(release) is dict and set(release) == {'provider', 'release_id', 'version',
            'date', 'artifact_sha256', 'provenance_reference', 'notice_reference'}
            and release.get('provider') == 'MTGJSON' and _sha(release.get('artifact_sha256'))
            and all(type(v) is str and 0 < len(v) <= 256 for v in release.values())
            and canonical(release) == self.release_json, 'closed canonical release binding required')
        _check(_sha(self.provenance_sha256) and _sha(self.notice_sha256)
               and _reference(self.internal_decision_reference), 'independent control pins required')
        _check(self.material in ('ORIGINAL_PROJECT_FIXTURE', 'MIXED_MTGJSON_RELEASE'), 'explicit material required')
        _check(type(self.bases) is tuple and 0 < len(self.bases) <= 16
               and all(type(b) is SourceUseBasis for b in self.bases), 'bounded host evidence required')
        for basis in self.bases:
            basis.validate()
        _check(len({b.reference for b in self.bases}) == len(self.bases), 'duplicate evidence reference')
        # Authoring a fixture establishes no rights in real provider data.
        _check(self.material != 'MIXED_MTGJSON_RELEASE'
               or all(b.kind != 'PROJECT_AUTHORSHIP' for b in self.bases), 'fixture basis cannot authorize real data')

    def require_supported(self):
        self.validate()
        for operation in OPERATIONS:
            scope = ('FACTUAL_PROJECTION', 'COMPLETE_ARTIFACT') if operation in (
                'PRIVATE_FACTUAL_RETENTION', 'PRIVATE_REPORTS') else ('COMPLETE_ARTIFACT',)
            evidence = [b for b in self.bases if operation in b.operations and b.material_scope in scope]
            _check(not any(b.disposition == 'EXPRESSLY_RESTRICTED' for b in evidence),
                   'express restriction conflicts with requested operation: ' + operation)
            _check(any(b.disposition == 'SUPPORTED' and b.kind != 'INTERNAL_POLICY' for b in evidence),
                   'supported source-use basis missing for ' + operation)

    def receipt(self):
        self.validate()
        body = dict(schema_version='private-mtgjson-source-profile-v1', release=json.loads(self.release_json),
            provenance_sha256=self.provenance_sha256, notice_sha256=self.notice_sha256,
            bases=[json.loads(canonical(asdict(b))) for b in self.bases],
            internal_decision_reference=self.internal_decision_reference,
            material=self.material, retention_profile=RETENTION,
            retained_fields=sorted(FACTUAL_FIELDS), retained_identifier_namespaces=sorted(IDENTIFIERS),
            authority='HOST_DISPOSITION_NOT_EXTERNAL_LICENSE', canonical_admission=False,
            real_card_execution=False, public_export=False, external_ai_export=False)
        return dict(body, profile_id='sha256:' + digest(body))

    def __call__(self, bindings):
        """Compatible with existing authorizer callbacks; full-retention calls refuse.

        In particular this profile cannot authorize set-preparation's full candidate
        retention or the legacy reconciliation contract by accident.
        """
        from .reconciliation import OPERATION
        self.require_supported()
        keys = {'operation', 'release', 'limits', 'whole_artifact_read',
            'private_source_and_derived_retention', 'public_export', 'canonical_admission',
            'retention_profile', 'source_use_receipt'}
        return (type(bindings) is dict and set(bindings) == keys
            and bindings['operation'] == OPERATION and bindings['release'] == json.loads(self.release_json)
            and bindings['retention_profile'] == RETENTION and bindings['source_use_receipt'] == self.receipt()
            and bindings['whole_artifact_read'] is True
            and bindings['private_source_and_derived_retention'] is True
            and bindings['public_export'] is False and bindings['canonical_admission'] is False)


def project_row(raw):
    """Retain only explicitly scoped fields, not arbitrary source-valued field names.

    This runs AFTER authorization for whole-input reads/temporary mixed processing.
    Field placement is not proof of factual truth or an external rights grant.
    """
    if type(raw) is not dict:
        return raw, 0
    selected = {k: v for k, v in raw.items() if k in FACTUAL_FIELDS}
    lists = {'colors', 'colorIdentity', 'types', 'subtypes', 'supertypes', 'finishes', 'otherFaceIds'}
    for key, value in selected.items():
        if key in lists:
            _check(type(value) is list and len(value) <= 128
                   and all(type(x) is str and len(x) <= 256 for x in value), 'invalid factual list field')
        elif key == 'manaValue':
            _check(type(value) in (int, float) and 0 <= value <= 1000 and math.isfinite(value),
                   'invalid factual numeric field')
        else:
            _check(type(value) is str and len(value) <= 1024, 'invalid factual string field')
    omitted = len(set(raw) - FACTUAL_FIELDS - {'identifiers'})
    ids = raw.get('identifiers', {})
    if type(ids) is dict:
        selected['identifiers'] = {k: v for k, v in ids.items() if k in IDENTIFIERS}
        omitted += len(set(ids) - IDENTIFIERS)
    else:
        selected['identifiers'] = ids  # Let the existing validator refuse malformed identity data.
    return selected, omitted
