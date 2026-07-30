"""Pure adapters from retained v1 canonical records to the typed v2 contract."""
from __future__ import annotations
from typing import Any, Mapping
from canonical import PackDefinition, PackSlot, Product, ProductComponent, ProductVersion, Sheet, SheetEntry


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
