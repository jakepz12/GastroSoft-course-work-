from pathlib import Path


def load_style(*relative_parts: str) -> str:
    base_dir = Path(__file__).resolve().parent
    style_path = base_dir.joinpath(*relative_parts)
    return style_path.read_text(encoding="utf-8")

