"""Evidence and claim governance bounded context.

The enterprise governance extension is mounted here so requirements, traceability,
impact decisions, and workflow cases remain adjacent to the evidence boundary
without expanding application bootstrap wiring.
"""

from tdp.modules.evidence.presentation.http.router import router as _evidence_router
from tdp.modules.governance.presentation.http.router import router as _governance_router

_evidence_router.include_router(_governance_router)
