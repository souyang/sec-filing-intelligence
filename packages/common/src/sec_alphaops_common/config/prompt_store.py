from __future__ import annotations

from pathlib import Path


class PromptTemplateStore:
    """Loads versioned prompt templates from packages/langgraph/prompts/."""

    def __init__(self, prompts_root: Path | None = None) -> None:
        if prompts_root is None:
            # packages/langgraph/prompts relative to repo root
            prompts_root = Path(__file__).resolve().parents[4] / "langgraph" / "prompts"
        self._root = prompts_root

    def resolve_path(self, filing_type: str, node_name: str, version: str | None = None) -> Path:
        node_dir = self._root / filing_type / node_name
        if not node_dir.exists():
            raise FileNotFoundError(f"No prompts for {filing_type}/{node_name} at {node_dir}")

        if version is not None:
            path = node_dir / f"v{version.lstrip('v')}.txt"
            if not path.exists():
                raise FileNotFoundError(f"Prompt version not found: {path}")
            return path

        versions = sorted(node_dir.glob("v*.txt"), reverse=True)
        if not versions:
            raise FileNotFoundError(f"No prompt versions in {node_dir}")
        return versions[0]

    def load(self, filing_type: str, node_name: str, version: str | None = None) -> str:
        return self.resolve_path(filing_type, node_name, version).read_text(encoding="utf-8")
