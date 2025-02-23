# Repoprompt

Repoprompt is a Python library that concatenates an entire code repository's files into a suitable text prompt for use with Large Language Models (LLMs). It provides a simple way to prepare your codebase for analysis or discussion with LLMs by converting your repository structure into a standardized text format.

## Features

- Generates a complete repository overview including file tree and contents
- Intelligent file filtering:
  - Automatically detects and skips binary files
  - Respects `.gitignore` patterns
  - Optional inclusion of hidden files
  - Support for include/exclude patterns using regex
- Flexible output options: print to console or save to file
- Clean, standardized output format suitable for LLM prompts

## Installation

You can install repoprompt using pip:

```bash
pip install repoprompt
```

## Usage

### Command Line Interface

The basic command to process a repository:

```bash
python -m repoprompt /path/to/repository
```

Available options:

```bash
Options:
  --hidden          Include hidden files
  --include TEXT    Only include files matching regex pattern
  --exclude TEXT    Exclude files matching regex pattern
  --no-gitignore    Disable .gitignore processing
  --out-file PATH   Output file path
  --help            Show this message and exit
```

### Examples

Process a repository and print to console:
```bash
python -m repoprompt /path/to/repo
```

Include hidden files:
```bash
python -m repoprompt /path/to/repo --hidden
```

Only include Python files:
```bash
python -m repoprompt /path/to/repo --include "\.py$"
```

Exclude test files:
```bash
python -m repoprompt /path/to/repo --exclude "test_.*\.py$"
```

Save output to a file:
```bash
python -m repoprompt /path/to/repo --out-file prompt.txt
```

### Python API

You can also use repoprompt programmatically:

```python
from pathlib import Path
from repoprompt import RepoPrompt

# Create an instance
rp = RepoPrompt()

# Generate prompt
prompt = rp(
    root_path=Path('/path/to/repo'),
    include_hidden=False,
    include_pattern=r'\.py$',
    exclude_pattern=None,
    use_gitignore=True
)

# Use the generated prompt
print(prompt)
```

## Output Format

The generated prompt follows this structure:

```
Absolute path to repository on disk:
/path/to/repository

File tree of repository:
./file1.txt
./dir/file2.py
...

----- ./file1.txt -----
[content of file1.txt]
----- END -----

----- ./dir/file2.py -----
[content of file2.py]
----- END -----
```

## Development

### Requirements

- Python 3.9 or higher
- Dependencies are managed with pip and defined in pyproject.toml

### Running Tests

Install development dependencies:
```bash
pip install repoprompt[dev]
```

Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
