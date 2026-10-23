"""Include site assets kept outside the notes directory."""

from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files


def on_files(files: Files, config: MkDocsConfig) -> Files:
    project_dir = Path(config.config_file_path).parent
    for asset in sorted((project_dir / "assets").rglob("*")):
        if asset.is_file():
            files.append(
                File(
                    asset.relative_to(project_dir).as_posix(),
                    src_dir=str(project_dir),
                    dest_dir=config.site_dir,
                    use_directory_urls=config.use_directory_urls,
                )
            )
    return files
