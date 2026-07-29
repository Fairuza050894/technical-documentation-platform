from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportOpenApiSourceCommand:
    project_id: str
    name: str
    file_name: str
    content: bytes
