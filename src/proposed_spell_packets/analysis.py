"""Read-only declared-dependency analysis of validated fictional v1 packets.

No prose is interpreted. Typed references describe authored dependencies, context
and limitations; none establishes truth, completeness, sufficiency or permission.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json

from . import validation as v


ANALYSIS_VERSION = "proposed-spell-dependency-report-v1"
REPORT_DOMAIN = ANALYSIS_VERSION
BOUNDARY = (
    "Declared dependencies may be incomplete. PRESENT means supplied, not verified. "
    "Absence of a listed barrier does not prove its absence in the game. Authored "
    "reasoning and conclusions are unverified prose; retained rules provide versioned "
    "context only. No sufficiency, legality, compatibility or permission verdict is made."
)
COLLECTIONS = (("claims", "claim_id", "claim"), ("reasoning", "step_id", "step"),
               ("choices", "choice_id", "choice"), ("limitations", "limitation_id", "limitation"),
               ("contexts", "context_id", "context"), ("rule_evidence", "evidence_id", "rule"))


@dataclass(frozen=True)
class DerivedReport:
    """Privately owned immutable canonical bytes; every dictionary read is a copy."""

    canonical_bytes: bytes

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def report_id(self):
        return self.to_dict()["report_id"]


def _report(kind, packets, analyses, **extra):
    value = {"analysis_version": ANALYSIS_VERSION, "report_kind": kind,
             "authority": "DECLARED_DEPENDENCIES_ONLY", "execution_authority": "BLOCKED",
             "boundary": BOUNDARY, "inputs": [_binding(packet) for packet in packets],
             "analyses": analyses, **extra}
    value["report_id"] = v.identity(REPORT_DOMAIN, value, "report_id")
    return DerivedReport(v._canonical_candidate(value))


def _binding(packet):
    return {key: packet[key] for key in
            ("packet_id", "contract_id", "schema_version", "lineage_id", "revision")}


def _read(workspace, identity):
    # Actual files, retained bindings, exact permitted roots and all required
    # ancestors are checked on every invocation at the corrected shared boundary.
    packet, history = workspace.read(identity)
    return v.snapshot(packet), v.snapshot(history)


def _ordered_history(packet, history):
    rows = [packet]
    while rows[-1]["history"]["supersedes_packet_ids"]:
        rows.append(history[rows[-1]["history"]["supersedes_packet_ids"][0]])
    return list(reversed(rows))


def _observations(packet, history):
    origins = {}
    for row in _ordered_history(packet, history):
        for observation in row["history"]["review_observations"]:
            origins.setdefault(observation["observation_id"], {
                "origin_packet_id": row["packet_id"], "origin_revision": row["revision"]})
    return [{"observation": observation, **origins[observation["observation_id"]]}
            for observation in packet["history"]["review_observations"]]


def _analyze(packet, history):
    indexes = {kind: {row[field]: row for row in packet[name]}
               for name, field, kind in COLLECTIONS}
    nodes = {"conclusion": {"node": "conclusion", "kind": "conclusion",
                            "authored": packet["conclusion"]}}
    edges = []
    edge_keys = set()

    def add(kind, ref):
        node = kind + ":" + ref
        if node not in nodes:
            nodes[node] = {"node": node, "kind": kind, "authored": indexes[kind][ref]}
        return node

    def edge(source, kind, ref, relationship, position):
        target = add(kind, ref)
        key = (source, target, relationship, position)
        if key not in edge_keys:
            edge_keys.add(key)
            edges.append({"source": source, "target": target,
                          "relationship": relationship, "position": position})
        return target

    conclusion = packet["conclusion"]
    for field, kind, relation in (("step_refs", "step", "conclusion_step"),
                                  ("assumption_refs", "claim", "conclusion_assumption"),
                                  ("limitation_refs", "limitation", "conclusion_limitation")):
        for position, ref in enumerate(conclusion[field]):
            edge("conclusion", kind, ref, relation, position)

    # Core dependencies are deliberately separate from contextual choices and
    # limitation targets. A limitation discussing a claim does not assert it as
    # a premise, nor does sharing an alternative turn a choice into a premise.
    branches = []
    branch_paths = []
    branch_keys = []
    for ref in conclusion["step_refs"]:
        step = indexes["step"][ref]
        key = (step["context_id"], step["alternative_id"])
        if key not in branch_keys:
            branch_keys.append(key)
    core_nodes = set()
    for context, alternative in branch_keys:
        direct = [ref for ref in conclusion["step_refs"] if
                  (indexes["step"][ref]["context_id"], indexes["step"][ref]["alternative_id"])
                  == (context, alternative)]
        paths = {}
        pending = deque(("step", ref, ["conclusion", "step:" + ref]) for ref in direct)
        pending.extend(("claim", ref, ["conclusion", "claim:" + ref])
                       for ref in conclusion["assumption_refs"])
        while pending:
            kind, ref, path = pending.popleft()
            node = add(kind, ref)
            if node in paths:
                continue
            paths[node] = path
            core_nodes.add(node)
            row = indexes[kind][ref]
            if kind == "step":
                for position, claim in enumerate(row["claim_refs"]):
                    target = edge(node, "claim", claim, "step_claim", position)
                    pending.append(("claim", claim, path + [target]))
                for position, dependency in enumerate(row["depends_on_steps"]):
                    target = edge(node, "step", dependency, "depends_on_step", position)
                    pending.append(("step", dependency, path + [target]))
        steps = [row["step_id"] for row in packet["reasoning"] if "step:" + row["step_id"] in paths]
        claims = [row["claim_id"] for row in packet["claims"] if "claim:" + row["claim_id"] in paths]
        choices = [row["choice_id"] for row in packet["choices"] if
                   (row["context_id"], row["alternative_id"]) == (context, alternative)]
        branches.append({"context_id": context, "context_version": indexes["context"][context]["version"],
                         "alternative_id": alternative, "direct_step_refs": direct,
                         "transitive_step_refs": [ref for ref in steps if ref not in direct],
                         "claim_refs": claims,
                         "assumption_refs": [ref for ref in claims if
                                             indexes["claim"][ref]["basis"] == "AUTHORED_FICTIONAL_ASSUMPTION"],
                         "contextual_choice_refs": choices})
        branch_paths.append(paths)

    # Complete the displayed typed reference graph, including contextual and
    # limitation relationships. It is a finite node/edge listing, never a list
    # of every possible path through a diamond-shaped dependency graph.
    processed = set()
    while len(processed) < len(nodes):
        source = next(node for node in nodes if node not in processed)
        processed.add(source)
        kind = nodes[source]["kind"]
        row = nodes[source]["authored"]
        if kind in ("claim", "step", "choice"):
            edge(source, "context", row["context_id"], "context_binding", 0)
            if row["alternative_id"] is not None:
                for position, choice in enumerate(packet["choices"]):
                    if (choice["context_id"], choice["alternative_id"]) == (row["context_id"], row["alternative_id"]):
                        edge(source, "choice", choice["choice_id"], "alternative_context", position)
        relations = {
            "claim": (("rule_context_refs", "rule", "claim_rule_context"),
                      ("limitation_refs", "limitation", "claim_limitation")),
            "step": (("claim_refs", "claim", "step_claim"),
                     ("depends_on_steps", "step", "depends_on_step"),
                     ("rule_refs", "rule", "step_rule_context"),
                     ("limitation_refs", "limitation", "step_limitation")),
            "choice": (("claim_refs", "claim", "choice_context_claim"),),
            "limitation": (("claim_refs", "claim", "limitation_claim_target"),
                           ("step_refs", "step", "limitation_step_target"),
                           ("context_ids", "context", "limitation_context")),
        }
        for field, target_kind, relation in relations.get(kind, ()):
            for position, ref in enumerate(row[field]):
                edge(source, target_kind, ref, relation, position)

    def binding(branch):
        return {key: branch[key] for key in ("context_id", "context_version", "alternative_id")}

    findings = []
    for node, value in nodes.items():
        if node not in core_nodes or value["authored"].get("condition") == "PRESENT":
            continue
        affected = [index for index, paths in enumerate(branch_paths) if node in paths]
        findings.append({"node": node, "condition": value["authored"]["condition"],
                         "branches": [binding(branches[index]) for index in affected],
                         "witness_paths": [{"branch": binding(branches[index]),
                                            "nodes": branch_paths[index][node]} for index in affected]})

    limitations = []
    for ref in conclusion["limitation_refs"]:
        row = indexes["limitation"][ref]
        node = "limitation:" + ref
        affected = []
        for index, branch in enumerate(branches):
            if branch["context_id"] not in row["context_ids"]:
                continue
            targets = [indexes["claim"][key] for key in row["claim_refs"]]
            targets += [indexes["step"][key] for key in row["step_refs"]]
            if not targets or any(target["context_id"] == branch["context_id"] and
                                  target["alternative_id"] in (None, branch["alternative_id"])
                                  for target in targets):
                affected.append(index)
        limitations.append({"node": node, "limitation": row,
                            "declared_on_conclusion": True,
                            "conclusion_witness_path": ["conclusion", node],
                            "conclusion_declared_branches": [binding(branch) for branch in branches
                                                             if branch["context_id"] in row["context_ids"]],
                            "scope_note": "Branches follow declared target scope; the conclusion citation remains even when no selected branch matches its targets.",
                            "branches": [binding(branches[index]) for index in affected],
                            "witness_paths": [{"branch": binding(branches[index]),
                                               "nodes": ["conclusion", node]} for index in affected]})

    uncited = {}
    for name, field, kind in COLLECTIONS:
        if kind in ("claim", "step"):
            # Contextual/limitation-only rows remain uncited logical content even
            # when displayed as targets elsewhere in the typed graph.
            uncited[name] = [row for row in packet[name] if kind + ":" + row[field] not in core_nodes]
        else:
            uncited[name] = [row for row in packet[name] if kind + ":" + row[field] not in nodes]
    return {"input": _binding(packet), "authored_question": packet["question"],
            "authored_conclusion": conclusion,
            "contexts": [row for row in packet["contexts"] if "context:" + row["context_id"] in nodes],
            "branches": branches, "nodes": list(nodes.values()), "edges": edges,
            "condition_findings": findings, "declared_limitations": limitations,
            "retained_rule_context": [row for row in packet["rule_evidence"] if "rule:" + row["evidence_id"] in nodes],
            "uncited_packet_content": uncited, "review_observations": _observations(packet, history)}


def analyze(workspace, identity):
    """Analyze one explicitly selected recorded identity without writing files."""
    packet, history = _read(workspace, identity)
    return _report("ANALYSIS", [packet], [_analyze(packet, history)])


def _impact(analysis, node):
    edges = analysis["edges"]
    reverse = {}
    for edge in edges:
        if edge["relationship"] in ("step_claim", "depends_on_step"):
            reverse.setdefault(edge["target"], []).append(edge["source"])
    pending, affected = deque([node]), set()
    while pending:
        current = pending.popleft()
        for source in reverse.get(current, []):
            if source not in affected:
                affected.add(source)
                pending.append(source)
    if node.startswith("step:"):
        affected.add(node)
    branches = [branch for branch in analysis["branches"] if
                (node.startswith("claim:") and node[6:] in branch["claim_refs"]) or
                any(step[5:] in branch["direct_step_refs"] + branch["transitive_step_refs"] for step in affected)]
    # A changed retained citation, context, choice or limitation also has a
    # structural association. Keep these typed paths separate from the logical
    # dependency impact above, so context does not become a new premise.
    all_reverse = {}
    for edge in edges:
        all_reverse.setdefault(edge["target"], []).append(edge)
    paths = {node: ([node], [])}
    pending = deque([node])
    while pending:
        current = pending.popleft()
        for edge in all_reverse.get(current, []):
            source = edge["source"]
            if source in paths:
                continue
            nodes, relationships = paths[current]
            paths[source] = ([source] + nodes, [edge["relationship"]] + relationships)
            pending.append(source)
    associations = []
    for branch in analysis["branches"]:
        scope = {key: branch[key] for key in ("context_id", "context_version", "alternative_id")}
        for step in branch["direct_step_refs"] + branch["transitive_step_refs"]:
            source = "step:" + step
            if source in paths:
                nodes, relationships = paths[source]
                associations.append({"branch": scope, "source": source,
                                     "nodes": nodes, "relationships": relationships})
    declared_branches = [branch for limitation in analysis["declared_limitations"]
                         if limitation["node"] == node for branch in limitation["branches"]]
    associated_branches = []
    for branch in [*(row["branch"] for row in associations), *declared_branches]:
        if branch not in associated_branches:
            associated_branches.append(branch)
    return {"dependent_step_refs": [value["authored"]["step_id"] for value in analysis["nodes"] if
                                    value["kind"] == "step" and value["node"] in affected],
            "branches": [{key: branch[key] for key in ("context_id", "context_version", "alternative_id")}
                         for branch in branches],
            "reference_associations": associations, "associated_branches": associated_branches,
            "conclusion_reference_path": paths.get("conclusion", ([], []))[0],
            "association_boundary": "Typed reference associations are not additional logical premises."}


def _same(left, right):
    return v._canonical_candidate(left) == v._canonical_candidate(right)


def _changes(before, after):
    return [{"field": key, "before": before.get(key), "after": after.get(key)}
            for key in dict.fromkeys([*before, *after]) if
            key not in before or key not in after or not _same(before[key], after[key])]


def compare(workspace, ancestor_identity, descendant_identity):
    """Compare explicitly ordered compatible ancestors, never infer a latest."""
    ancestor, ancestor_history = _read(workspace, ancestor_identity)
    descendant, descendant_history = _read(workspace, descendant_identity)
    if any(ancestor[key] != descendant[key] for key in ("contract_id", "schema_version", "lineage_id")):
        v.fail("ANALYSIS_INCOMPATIBLE_LINEAGE_OR_CONTRACT")
    if ancestor_identity != descendant_identity and ancestor_identity not in descendant_history:
        v.fail("ANALYSIS_EXPLICIT_ANCESTOR_REQUIRED")
    if ancestor_identity in descendant_history and not _same(ancestor, descendant_history[ancestor_identity]):
        v.fail("ANALYSIS_ANCESTOR_BYTES_CHANGED")
    before = _analyze(ancestor, ancestor_history)
    after = _analyze(descendant, descendant_history)
    changes = {}
    for name, field, kind in COLLECTIONS:
        old = {row[field]: row for row in ancestor[name]}
        new = {row[field]: row for row in descendant[name]}
        rows = []
        for ref in dict.fromkeys([*old, *new]):
            if ref in old and ref in new and _same(old[ref], new[ref]):
                continue
            node = kind + ":" + ref
            rows.append({"node": node, "change": "ADDED" if ref not in old else
                         "ABSENT_FROM_SUCCESSOR" if ref not in new else "CHANGED",
                         "before": old.get(ref), "after": new.get(ref),
                         "changed_fields": _changes(old.get(ref, {}), new.get(ref, {})),
                         "structural_impact": {"ancestor": _impact(before, node),
                                               "descendant": _impact(after, node)}})
        changes[name] = rows
    changes["assumptions"] = [row for row in changes["claims"] if any(
        value is not None and value["basis"] == "AUTHORED_FICTIONAL_ASSUMPTION"
        for value in (row["before"], row["after"]))]
    changes["collection_order"] = [{"collection": name,
                                    "ancestor": [row[field] for row in ancestor[name]],
                                    "descendant": [row[field] for row in descendant[name]]}
                                   for name, field, _ in COLLECTIONS if
                                   [row[field] for row in ancestor[name]] != [row[field] for row in descendant[name]]]
    changes["authored_conclusion"] = _changes(ancestor["conclusion"], descendant["conclusion"])
    changes["other_authored_fields"] = _changes(
        {key: value for key, value in ancestor.items() if key not in
         {"packet_id", "revision", "history", "conclusion", *(name for name, _, _ in COLLECTIONS)}},
        {key: value for key, value in descendant.items() if key not in
         {"packet_id", "revision", "history", "conclusion", *(name for name, _, _ in COLLECTIONS)}})
    for name in ("condition_findings", "declared_limitations"):
        changes[name] = {"no_longer_reported": [row for row in before[name] if not any(_same(row, new) for new in after[name])],
                         "newly_reported": [row for row in after[name] if not any(_same(row, old) for old in before[name])]}
    old = {row["observation"]["observation_id"]: row for row in before["review_observations"]}
    new = {row["observation"]["observation_id"]: row for row in after["review_observations"]}
    changes["review_observations"] = {
        "added": [row for ref, row in new.items() if ref not in old],
        "absent_from_successor": [row for ref, row in old.items() if ref not in new],
        "retained": [row for ref, row in new.items() if ref in old],
        "historical_notice": "An observation absent from the successor remains in its ancestor; no history was deleted.",
        "order_changed": list(old) != list(new)}
    material = lambda packet: {key: value for key, value in packet.items() if key not in ("packet_id", "revision", "history")}
    material_changed = not _same(material(ancestor), material(descendant))
    return _report("COMPARISON", [ancestor, descendant], [before, after], changes=changes,
                   no_change=ancestor_identity == descendant_identity,
                   reviewed_material_changed=material_changed,
                   review_only_change=not material_changed and not _same(
                       ancestor["history"]["review_observations"], descendant["history"]["review_observations"]),
                   comparison_boundary="Observed edits and structural dependencies only; no new assertion or reasoning is verified.")


def render(report):
    """Readable representation of the same deterministic derived report."""
    value = report.to_dict()
    lines = [f'{value["report_kind"]}: {value["report_id"]}',
             f'Analysis version: {value["analysis_version"]}',
             'Authority: DECLARED_DEPENDENCIES_ONLY | Execution authority: BLOCKED', value["boundary"]]
    for analysis in value["analyses"]:
        lines += ["", "Packet: " + json.dumps(analysis["input"], sort_keys=True),
                  "Authored conclusion: " + json.dumps(analysis["authored_conclusion"], ensure_ascii=False, sort_keys=True)]
        for name, label in (("branches", "Separate declared branches"),
                            ("condition_findings", "Claim/step condition findings"),
                            ("declared_limitations", "Author-declared limitations"),
                            ("nodes", "Typed nodes (authored content; assumptions distinguished by basis)"),
                            ("edges", "Typed reference edges (position preserves authored reference order)"),
                            ("review_observations", "Fictional review observations and historical origins"),
                            ("uncited_packet_content", "Uncited packet content (not direct conclusion dependencies)")):
            lines.append(label + ":")
            rows = analysis[name] if type(analysis[name]) is list else [analysis[name]]
            lines.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
            if not rows:
                lines.append("(none declared)")
    if value["report_kind"] == "COMPARISON":
        lines += ["", value["comparison_boundary"],
                  f'No change: {value["no_change"]} | Reviewed material changed: {value["reviewed_material_changed"]} | Review-only change: {value["review_only_change"]}']
        for name, changes in value["changes"].items():
            lines.append("Observed " + name + " changes: " + json.dumps(changes, ensure_ascii=False, sort_keys=True))
        lines.append("The author supplied any changed claim value; no truth or soundness is established. A limitation absent from the successor is no longer declared there.")
    return "\n".join(lines)
