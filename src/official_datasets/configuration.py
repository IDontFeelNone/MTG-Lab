"""Reviewed configuration for official, non-canonical reference datasets."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DatasetDefinition:
    name: str
    provider: str
    official_url: str
    expected_filename: str
    expected_compression: str
    checksum_url: str | None
    local_storage_path: str
    schema_version: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


_DEFINITIONS = (
    DatasetDefinition(
        name="mtgjson",
        provider="mtgjson",
        official_url="https://mtgjson.com/api/v5/AllPrintings.json",
        expected_filename="AllPrintings.json",
        expected_compression="none",
        checksum_url=None,
        local_storage_path="reference-datasets/mtgjson/all-printings",
        schema_version="5.x",
    ),
)


def definitions() -> tuple[DatasetDefinition, ...]:
    return _DEFINITIONS


def get_definition(name: str) -> DatasetDefinition:
    try:
        return next(item for item in _DEFINITIONS if item.name == name.casefold())
    except StopIteration as error:
        raise ValueError(f"unsupported official reference dataset: {name}") from error
