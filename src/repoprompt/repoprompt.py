from pathlib import Path
import re
from typing import List, Optional

import click


class RepoPrompt:
    def __init__(
        self,
    ):
        pass

    def is_binary_file(
        self,
        file_path: Path
    ) -> bool:
        """
        Check if a file is binary by reading its first chunk and looking for null bytes
        and other indicators of binary content.
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check for null bytes which are common in binary files
                if b'\x00' in chunk:
                    return True
                # Try to decode as text
                try:
                    chunk.decode('utf-8')
                    return False
                except UnicodeDecodeError:
                    return True
        except IOError:
            return False

    def should_ignore_file(
        self,
        path: Path,
        gitignore_patterns: List[str]
    ) -> bool:
        """
        Check if file should be ignored based on gitignore patterns.
        """
        if not gitignore_patterns:
            return False

        # Convert path to relative string for pattern matching
        rel_path = str(path)

        for pattern in gitignore_patterns:
            # Convert gitignore glob pattern to regex
            regex_pattern = pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
            if re.match(regex_pattern, rel_path):
                return True
        return False

    def read_gitignore(
        self,
        root_path: Path
    ) -> List[str]:
        """
        Read and parse .gitignore file, ignoring commented lines.
        """
        gitignore_path = root_path / '.gitignore'
        if not gitignore_path.exists():
            return []

        with open(gitignore_path, 'r') as f:
            patterns = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
        return patterns

    def get_file_tree(
        self,
        root_path: Path,
        include_hidden: bool = False,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
        use_gitignore: bool = True
    ) -> List[Path]:
        """
        Generate list of files to process based on given criteria.
        """
        files = []
        gitignore_patterns = self.read_gitignore(root_path) if use_gitignore else []

        for path in root_path.rglob('*'):
            if not path.is_file():
                continue

            # Skip binary files
            if self.is_binary_file(path):
                continue

            rel_path = path.relative_to(root_path)
            str_path = str(rel_path)

            # Skip hidden files unless explicitly included
            if not include_hidden and (path.name.startswith('.') or any(p.startswith('.') for p in path.parts)):
                continue

            # Check include pattern
            if include_pattern and not re.search(include_pattern, str_path):
                continue

            # Check exclude pattern
            if exclude_pattern and re.search(exclude_pattern, str_path):
                continue

            # Check gitignore patterns
            if use_gitignore and self.should_ignore_file(rel_path, gitignore_patterns):
                continue

            files.append(rel_path)

        return sorted(files)

    def __call__(
        self,
        root_path: Path,
        include_hidden: bool = False,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
        use_gitignore: bool = True
    ) -> str:
        """
        Generate the complete prompt text.
        """
        files = self.get_file_tree(
            root_path,
            include_hidden,
            include_pattern,
            exclude_pattern,
            use_gitignore
        )

        # Build output string
        output = [f"Absolute path to repository on disk:\n{root_path.absolute()}\n\nFile tree of repository:"]

        # Add file tree
        for file_path in files:
            output.append(f"./{file_path}")
        output.append("")

        # Add file contents
        for file_path in files:
            full_path = root_path / file_path
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                output.extend([
                    f"----- ./{file_path} -----",
                    content.rstrip(),
                    "----- END -----\n"
                ])
            except UnicodeDecodeError:
                continue

        return '\n'.join(output)


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--hidden', is_flag=True, help='Include hidden files')
@click.option('--include', help='Only include files matching regex pattern')
@click.option('--exclude', help='Exclude files matching regex pattern')
@click.option('--no-gitignore', is_flag=True, help='Disable .gitignore processing')
@click.option('--out-file', type=click.Path(), help='Output file path')
def cli(
    path: str,
    hidden: bool,
    include: Optional[str],
    exclude: Optional[str],
    no_gitignore: bool,
    out_file: Optional[str]
):
    """
    Generate LLM prompt from directory contents.
    """
    root_path = Path(path)

    rp = RepoPrompt()
    prompt = rp(
        root_path,
        include_hidden=hidden,
        include_pattern=include,
        exclude_pattern=exclude,
        use_gitignore=not no_gitignore
    )

    if out_file:
        with open(out_file, 'w') as f:
            f.write(prompt)
    else:
        print(prompt)


if __name__ == '__main__':
    cli()
