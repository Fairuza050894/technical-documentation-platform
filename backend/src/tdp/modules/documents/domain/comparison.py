import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum

from tdp.modules.documents.domain.errors import InvalidDocumentVersionComparisonError

_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
_KEY_PATTERN = re.compile(r"[^a-z0-9]+")


class DocumentSectionChangeKind(StrEnum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    REMOVED = "REMOVED"


@dataclass(frozen=True, slots=True)
class DocumentSection:
    key: str
    title: str
    content: str
    checksum: str


@dataclass(frozen=True, slots=True)
class DocumentSectionChange:
    section_key: str
    section_title: str
    kind: DocumentSectionChangeKind
    before_checksum: str
    after_checksum: str
    before_excerpt: str
    after_excerpt: str


@dataclass(frozen=True, slots=True)
class DocumentVersionComparison:
    baseline_version_id: str
    target_version_id: str
    document_id: str
    changes: tuple[DocumentSectionChange, ...]

    @property
    def added_total(self) -> int:
        return sum(change.kind is DocumentSectionChangeKind.ADDED for change in self.changes)

    @property
    def modified_total(self) -> int:
        return sum(change.kind is DocumentSectionChangeKind.MODIFIED for change in self.changes)

    @property
    def removed_total(self) -> int:
        return sum(change.kind is DocumentSectionChangeKind.REMOVED for change in self.changes)


class DeterministicMarkdownSectionComparator:
    def compare(
        self,
        *,
        baseline_version_id: str,
        target_version_id: str,
        document_id: str,
        baseline_content: str,
        target_content: str,
    ) -> DocumentVersionComparison:
        if baseline_version_id == target_version_id:
            raise InvalidDocumentVersionComparisonError(
                "Baseline and target document versions must be different."
            )

        before = {section.key: section for section in self._sections(baseline_content)}
        after = {section.key: section for section in self._sections(target_content)}
        changes: list[DocumentSectionChange] = []

        for key in sorted(before.keys() | after.keys()):
            old = before.get(key)
            new = after.get(key)
            if old is None and new is not None:
                changes.append(
                    DocumentSectionChange(
                        section_key=key,
                        section_title=new.title,
                        kind=DocumentSectionChangeKind.ADDED,
                        before_checksum="",
                        after_checksum=new.checksum,
                        before_excerpt="",
                        after_excerpt=self._excerpt(new.content),
                    )
                )
            elif old is not None and new is None:
                changes.append(
                    DocumentSectionChange(
                        section_key=key,
                        section_title=old.title,
                        kind=DocumentSectionChangeKind.REMOVED,
                        before_checksum=old.checksum,
                        after_checksum="",
                        before_excerpt=self._excerpt(old.content),
                        after_excerpt="",
                    )
                )
            elif old is not None and new is not None and old.checksum != new.checksum:
                changes.append(
                    DocumentSectionChange(
                        section_key=key,
                        section_title=new.title,
                        kind=DocumentSectionChangeKind.MODIFIED,
                        before_checksum=old.checksum,
                        after_checksum=new.checksum,
                        before_excerpt=self._excerpt(old.content),
                        after_excerpt=self._excerpt(new.content),
                    )
                )

        return DocumentVersionComparison(
            baseline_version_id=baseline_version_id,
            target_version_id=target_version_id,
            document_id=document_id,
            changes=tuple(changes),
        )

    def _sections(self, content: str) -> tuple[DocumentSection, ...]:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.splitlines()
        raw_sections: list[tuple[str, list[str]]] = []
        current_title = "Document preamble"
        current_lines: list[str] = []

        for line in lines:
            heading = _HEADING_PATTERN.match(line)
            if heading is not None:
                if current_lines:
                    raw_sections.append((current_title, current_lines))
                current_title = heading.group(1).strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            raw_sections.append((current_title, current_lines))

        sections: list[DocumentSection] = []
        seen_keys: set[str] = set()
        for title, section_lines in raw_sections:
            section_content = "\n".join(line.rstrip() for line in section_lines).strip() + "\n"
            key = self._key(title)
            if key in seen_keys:
                raise InvalidDocumentVersionComparisonError(
                    f"Document section key {key!r} is duplicated and cannot be compared."
                )
            seen_keys.add(key)
            sections.append(
                DocumentSection(
                    key=key,
                    title=title,
                    content=section_content,
                    checksum=hashlib.sha256(section_content.encode("utf-8")).hexdigest(),
                )
            )
        return tuple(sections)

    @staticmethod
    def _key(title: str) -> str:
        normalized = _KEY_PATTERN.sub("-", title.casefold()).strip("-")
        return normalized or "untitled-section"

    @staticmethod
    def _excerpt(content: str) -> str:
        normalized = " ".join(content.split())
        return normalized if len(normalized) <= 240 else normalized[:237] + "..."
