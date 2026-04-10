from __future__ import annotations

from .models import DossierResult, ProjectBrief
from .pipeline import DossierPipeline
from .providers import ProviderRegistry
from .service import DossierService

__all__ = [
    "__version__",
    "DossierPipeline",
    "DossierResult",
    "ProviderRegistry",
    "DossierService",
    "ProjectBrief",
]

__version__ = "0.1.0"
