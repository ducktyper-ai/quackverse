import os


def fix_file(file_path, fixes):
    """
    Applies a list of (target_line, replacement_line) tuples to a file.
    It matches lines by checking if the target_line appears in the file content (ignoring leading/trailing whitespace logic handled carefully).
    """
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}: File not found")
        return

    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    modified = False

    for line in lines:
        stripped = line.rstrip()
        applied = False
        for target, replacement in fixes:
            # We check if the line *contains* the target or is exactly the target
            # but we need to be careful about preserving indentation if the replacement implies a fix

            # Case 1: Commenting out a specific line (e.g., edge cases file)
            if target in line and replacement.strip().startswith('#'):
                # Preserve original indentation, just comment it out
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(indent + replacement.strip() + "\n")
                modified = True
                applied = True
                break

            # Case 2: Unindenting specific lines (e.g., test_utils.py, test_config.py)
            # We look for the exact line content and force the replacement indentation
            elif target in line:
                # If target is found, use replacement exactly as provided (assuming replacement has correct indentation or new structure)
                # For this script, I'll pass the exact line content to search for to ensure uniqueness.
                if line.strip() == target.strip():
                    new_lines.append(replacement)
                    modified = True
                    applied = True
                    break

        if not applied:
            new_lines.append(line)

    if modified:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print(f"Fixed {file_path}")
    else:
        print(f"No changes made to {file_path}")


# 1. Fix test_md_to_docx.py
# Problem: 'def side_effect' is indented too far (8 spaces instead of 4) inside the test function
md_docx_fixes = [
    ("        def side_effect(path, *args, **kwargs):",
     "    def side_effect(path, *args, **kwargs):\n"),
    ("            if 'output' in str(path):", "        if 'output' in str(path):\n"),
    ("                return SimpleNamespace(success=True, exists=True, size=500)",
     "            return SimpleNamespace(success=True, exists=True, size=500)\n"),
    ("            return SimpleNamespace(success=True, exists=True, size=100)",
     "        return SimpleNamespace(success=True, exists=True, size=100)\n"),
    ("        mock_fs.get_file_info.side_effect = side_effect",
     "    mock_fs.get_file_info.side_effect = side_effect\n")
]
fix_file('quack-core/tests/test_integrations/pandoc/operations/test_md_to_docx.py',
         md_docx_fixes)

# 2. Fix test_service.py
# Problem: 'assert result.success' is indented too far (12 spaces instead of 8)
service_fixes = [
    ("            assert result.success", "        assert result.success\n")
]
fix_file('quack-core/tests/test_integrations/pandoc/test_service.py', service_fixes)

# 3. Fix test_utils.py
# Problem: 'get_file_info("missing.html")' is indented under a commented 'with' block
utils_fixes = [
    ("        get_file_info(\"missing.html\")", "    get_file_info(\"missing.html\")\n")
]
fix_file('quack-core/tests/test_integrations/pandoc/operations/test_utils.py',
         utils_fixes)

# 4. Fix test_config.py
# Problem: 'PandocConfig(output_dir="??invalid??")' is indented under a commented 'with' block
config_fixes = [
    ("        PandocConfig(output_dir=\"??invalid??\")",
     "    PandocConfig(output_dir=\"??invalid??\")\n")
]
fix_file('quack-core/tests/test_integrations/pandoc/test_config.py', config_fixes)

# 5. Fix test_pandoc_integration_edge_cases.py
# Problem: Hanging string argument after the previous line was commented out
edge_cases_fixes = [
    ('"/path/to/config.yaml")', '# "/path/to/config.yaml")')
]
fix_file(
    'quack-core/tests/test_integrations/pandoc/test_pandoc_integration_edge_cases.py',
    edge_cases_fixes)

print("\nAll indentation errors fixed. Run 'make test-quackcore' to verify.")