from dataclasses import dataclass

from tdp.modules.documents.domain.errors import DocumentSeparationOfDutiesError


@dataclass(frozen=True, slots=True)
class ApprovalContext:
    author_actor: str
    reviewer_actor: str
    verified_identity: bool


class DocumentApprovalPolicy:
    """Enterprise approval policy with a controlled local-development exception."""

    def validate(self, context: ApprovalContext) -> None:
        if not context.verified_identity:
            return
        if context.author_actor == context.reviewer_actor:
            raise DocumentSeparationOfDutiesError(
                "A verified identity cannot approve a document version it authored."
            )
