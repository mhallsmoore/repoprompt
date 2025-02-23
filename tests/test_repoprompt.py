from pathlib import Path

from click.testing import CliRunner

from repoprompt.repoprompt import RepoPrompt
from repoprompt.repoprompt import cli


def test_basic_file_tree(fs):
    # Create a mock file system
    fs.create_dir('/repo')
    fs.create_file('/repo/file1.txt', contents='content1')
    fs.create_file('/repo/file2.txt', contents='content2')

    rp = RepoPrompt()
    files = rp.get_file_tree(Path('/repo'))
    assert sorted([str(f) for f in files]) == ['file1.txt', 'file2.txt']


def test_hidden_files(fs):
    # Test hidden file handling
    fs.create_dir('/repo')
    fs.create_file('/repo/visible.txt', contents='visible')
    fs.create_file('/repo/.hidden', contents='hidden')

    rp = RepoPrompt()

    # Hidden files should be excluded by default
    files = rp.get_file_tree(Path('/repo'))
    assert [str(f) for f in files] == ['visible.txt']

    # Hidden files should be included when specified
    files = rp.get_file_tree(Path('/repo'), include_hidden=True)
    assert sorted([str(f) for f in files]) == ['.hidden', 'visible.txt']


def test_include_pattern(fs):
    fs.create_dir('/repo')
    fs.create_file('/repo/test1.py', contents='test1')
    fs.create_file('/repo/test2.py', contents='test2')
    fs.create_file('/repo/other.txt', contents='other')

    rp = RepoPrompt()
    files = rp.get_file_tree(Path('/repo'), include_pattern=r'\.py$')
    assert sorted([str(f) for f in files]) == ['test1.py', 'test2.py']


def test_exclude_pattern(fs):
    fs.create_dir('/repo')
    fs.create_file('/repo/keep1.txt', contents='keep1')
    fs.create_file('/repo/keep2.txt', contents='keep2')
    fs.create_file('/repo/exclude.tmp', contents='temp')

    rp = RepoPrompt()
    files = rp.get_file_tree(Path('/repo'), exclude_pattern=r'\.tmp$')
    assert sorted([str(f) for f in files]) == ['keep1.txt', 'keep2.txt']


def test_gitignore(fs):
    fs.create_dir('/repo')
    fs.create_file('/repo/.gitignore', contents='*.log\n#*.txt\n*.tmp')
    fs.create_file('/repo/file.txt', contents='text')
    fs.create_file('/repo/file.log', contents='log')
    fs.create_file('/repo/file.tmp', contents='temp')

    rp = RepoPrompt()

    # Files matching gitignore patterns should be excluded by default
    files = rp.get_file_tree(Path('/repo'))
    assert [str(f) for f in files] == ['file.txt']

    # Gitignore can be disabled
    files = rp.get_file_tree(Path('/repo'), use_gitignore=False)
    assert sorted([str(f) for f in files]) == ['file.log', 'file.tmp', 'file.txt']


def test_prompt_format(fs):
    fs.create_dir('/repo')
    fs.create_file('/repo/test.txt', contents='test content')

    rp = RepoPrompt()
    prompt = rp(Path('/repo'))
    expected_lines = [
        f"Absolute path to repository on disk:\n{Path('/repo').absolute()}",
        "\nFile tree of repository:",
        "./test.txt",
        "\n----- ./test.txt -----",
        "test content",
        "----- END -----\n"
    ]
    assert prompt == '\n'.join(expected_lines)


def test_cli(fs):
    runner = CliRunner()

    # Set up test files
    fs.create_dir('/repo')
    fs.create_file('/repo/visible.txt', contents='visible')
    fs.create_file('/repo/.hidden', contents='hidden')

    # Test basic CLI usage
    result = runner.invoke(cli, ['/repo'])
    assert result.exit_code == 0
    assert 'visible.txt' in result.output
    assert '.hidden' not in result.output

    # Test --hidden flag
    result = runner.invoke(cli, ['/repo', '--hidden'])
    assert result.exit_code == 0
    assert 'visible.txt' in result.output
    assert '.hidden' in result.output

    # Test --out-file option
    fs.create_dir('/output')
    result = runner.invoke(cli, ['/repo', '--out-file', '/output/result.txt'])
    assert result.exit_code == 0
    assert Path('/output/result.txt').exists()
    with open('/output/result.txt', 'r') as f:
        content = f.read()
        assert 'visible.txt' in content


def test_binary_files(fs):
    # Test that binary files are skipped without error
    fs.create_dir('/repo')
    fs.create_file('/repo/text.txt', contents='text')

    # Create a binary file with null bytes
    binary_content = bytes([0x00, 0x01, 0x02, 0x03])
    fs.create_file('/repo/binary.bin', contents=binary_content)

    rp = RepoPrompt()

    # Test binary file detection
    assert rp.is_binary_file(Path('/repo/binary.bin'))
    assert not rp.is_binary_file(Path('/repo/text.txt'))

    # Test binary file exclusion from prompt
    prompt = rp(Path('/repo'))
    assert 'text.txt' in prompt
    assert 'binary.bin' not in prompt


def test_is_binary_file(fs):
    # Additional test for binary file detection
    fs.create_dir('/repo')
    fs.create_file('/repo/text.txt', contents='Hello, world!')

    # Create various types of binary content
    null_content = bytes([0x00, 0x01, 0x02, 0x03])
    fs.create_file('/repo/null.bin', contents=null_content)

    non_utf8_content = bytes([0xFF, 0xFE, 0xFD])
    fs.create_file('/repo/non_utf8.bin', contents=non_utf8_content)

    rp = RepoPrompt()

    assert not rp.is_binary_file(Path('/repo/text.txt'))
    assert rp.is_binary_file(Path('/repo/null.bin'))
    assert rp.is_binary_file(Path('/repo/non_utf8.bin'))
