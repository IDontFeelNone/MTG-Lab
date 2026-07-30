"""Pure adapters from retained v1 canonical records to the typed v2 contract."""
from __future__ import annotations
from typing import Any, Mapping
from canonical import Card, Printing, PackDefinition, PackSlot, Product, ProductComponent, ProductVersion, Sheet, SheetEntry

CARD_FACTS = ("mana_cost", "mana_value", "colors", "color_identity", "type_line", "supertypes",
              "card_types", "subtypes", "oracle_text", "keywords", "power", "toughness",
              "loyalty", "defense", "legalities", "legality_references", "related_cards")
PRINTING_FACTS = ("rarity", "product_classification", "artist", "flavor_text", "printed_name",
                  "printed_text", "printed_type_line", "frame", "border", "finishes", "treatments",
                  "promotional_flags", "release_date", "external_identifiers", "image_references",
                  "collector_number_namespace")


def card_v3(document: Mapping[str, Any]) -> Card:
    """Project retained v1 and native v3 Cards without mutating their bytes."""
    return Card(id=str(document["id"]), metadata=dict(document.get("metadata", {})),
                game_id=str(document["game"]), name=str(document["name"]),
                normalized_name=str(document.get("normalized_name", document["name"])).casefold(),
                layout=str(document.get("layout", "normal")), faces=tuple(document.get("faces", ())),
                facts={key: document[key] for key in CARD_FACTS if key in document},
                assertions=tuple(document.get("assertions", ())), schema_version="v3")


def printing_v3(document: Mapping[str, Any]) -> Printing:
    """Project retained v1 and native v3 Printings into the reconciled model."""
    return Printing(id=str(document["id"]), metadata=dict(document.get("metadata", {})),
                    card_id=str(document["card_id"]), rarity_id=str(document.get("rarity", "")),
                    treatment_ids=tuple(map(str, document.get("treatments", ()))),
                    finish_ids=tuple(map(str, document.get("finishes", ()))),
                    set_id=str(document.get("set_id", document.get("set_code", ""))).casefold(),
                    collector_number=str(document.get("collector_number", "")),
                    language=str(document.get("language", "und")),
                    facts={key: document[key] for key in PRINTING_FACTS if key in document},
                    assertions=tuple(document.get("assertions", ())), schema_version="v3")


def product_v2(document: Mapping[str, Any]) -> Product:
    versions = tuple(map(str, document.get("version_ids", ())))
    if not versions and document.get("slot_ids"):
        versions = (f"{document['id']}.legacy-version",)
    return Product(str(document["id"]), dict(document.get("metadata", {})), str(document["game"]),
                   str(document["name"]), str(document["product_type"]), versions, "v2",
                   str(document.get("lifecycle_status", "foundation")))


def legacy_product_graph(document: Mapping[str, Any]) -> tuple[tuple[ProductVersion, ...], tuple[PackDefinition, ...]]:
    slots = tuple(map(str, document.get("slot_ids", ())))
    if not slots or document.get("version_ids"):
        return (), ()
    version_id = f"{document['id']}.legacy-version"; pack_id = f"{document['id']}.legacy-pack"
    version = ProductVersion(version_id, {"compatibility_source": "v1"}, str(document["id"]),
                             f"{document['name']} legacy version",
                             (ProductComponent("pack_definition", pack_id, 1),))
    pack = PackDefinition(pack_id, {"compatibility_source": "v1"}, version_id,
                          f"{document['name']} legacy pack", slots)
    return (version,), (pack,)


def slot_v2(document: Mapping[str, Any]) -> PackSlot:
    draw_count = int(document.get("draw_count", document.get("count", 1)))
    if draw_count < 1:
        raise ValueError("count must be positive")
    return PackSlot(str(document["id"]), dict(document.get("metadata", {})), str(document["name"]),
                    str(document.get("print_sheet_id", document.get("sheet_id"))),
                    draw_count,
                    bool(document.get("replacement", True)))


def sheet_v2(document: Mapping[str, Any]) -> Sheet:
    entries = tuple(SheetEntry(str(x["printing_id"]), int(x.get("weight", 1))) for x in document["entries"])
    return Sheet(str(document["id"]), dict(document.get("metadata", {})), str(document["name"]), entries)
