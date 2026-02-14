"""Generate API reference pages for mkdocstrings."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

src = Path("cocapi")

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src.parent)
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.with_suffix("").parts)

    if "__pycache__" in parts:
        continue

    if parts[-1] == "__init__":
        parts = parts[:-1]
        if not parts:
            parts = ("cocapi",)
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        if ident == "cocapi":
            fd.write("# API Reference\n\n")
            fd.write(
                "Full reference for all public modules in the `cocapi` package. "
                "Select a module from the navigation to view its documentation.\n\n"
            )
        fd.write(f"::: {ident}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.as_posix())

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
