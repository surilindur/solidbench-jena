from pathlib import Path
from json import loads
from typing import List

META_SUFFIX: str = "-meta.json"


def generate_key(path: Path) -> str:
    if not path.name.endswith(META_SUFFIX):
        return path.name
    prefix, query_type, template, instance = path.name.removesuffix(META_SUFFIX).split(
        "-"
    )
    if len(template) < 2:
        template = f"0{template}"
    key = "-".join((prefix, query_type, template, instance))
    print(key)
    return key


def generate_summary_readme(source: Path, target: Path) -> None:
    markdown_lines: List[str] = [
        "| Query | Success | Results | Time (s) |\n",
        "| - | - | -:| -:|\n",
    ]
    for fp in sorted(source.iterdir(), key=generate_key):
        if fp.name.endswith(META_SUFFIX):
            with open(fp, "r") as meta_file:
                meta = loads(meta_file.read())
            name = fp.name.removesuffix(META_SUFFIX)
            success = "yes" if meta["success"] else "no"
            time = round(meta["time_seconds"], 4)
            markdown_lines.append(
                f"| {name} | {success} | {meta["results"]} | {time} |\n"
            )
    with open(target, "w") as target_file:
        target_file.writelines(markdown_lines)


if __name__ == "__main__":
    source_dir = Path(__file__).parent.parent.joinpath("results")
    target_file = source_dir.joinpath("README.md")
    generate_summary_readme(source=source_dir, target=target_file)
