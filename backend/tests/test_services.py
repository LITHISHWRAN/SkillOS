from app.services import parse_skill, validate_skill, scan_security
import pytest

from app.services import (
    clean_model_markdown,
    scan_security,
    validate_skill,
)

VALID = '''---
name: react-code-review
description: Reviews React components for bugs and accessibility. Use during code reviews.
---
# React Code Review

## Workflow
1. Inspect the component.
2. Report evidence.
'''

def test_valid_skill():
    result = validate_skill(VALID, "react-code-review")
    assert result["valid"] is True
    assert result["metadata"]["name"] == "react-code-review"
    assert not [f for f in result["findings"] if f["severity"] == "error"]

def test_missing_description():
    content = '''---
name: demo-skill
---
# Demo
Instructions.
'''
    result = validate_skill(content)
    assert result["valid"] is False
    assert any(f["code"] == "MISSING_DESCRIPTION" for f in result["findings"])

def test_invalid_name_and_directory_mismatch():
    content = '''---
name: Bad--Name
description: A description long enough to explain what it does and when to use it.
---
# Title
'''
    result = validate_skill(content, "another-name")
    codes = {f["code"] for f in result["findings"]}
    assert "INVALID_NAME" in codes
    assert "CONSECUTIVE_HYPHENS" in codes
    assert "DIRECTORY_NAME_MISMATCH" in codes

def test_malformed_yaml():
    content = '''---
name: [oops
description: broken
---
# Title
'''
    result = validate_skill(content)
    assert result["valid"] is False
    assert any(f["code"] == "FRONTMATTER_ERROR" for f in result["findings"])

def test_missing_frontmatter():
    result = validate_skill("# Just markdown")
    assert result["valid"] is False
    assert any(f["code"] == "FRONTMATTER_ERROR" for f in result["findings"])

def test_security_scanner_flags_credential_and_destructive_patterns():
    content = "Read .env and then run rm -rf /tmp/example"
    results = scan_security(content)
    codes = {f["code"] for f in results}
    assert "POSSIBLE_SECRET_ACCESS" in codes
    assert "DESTRUCTIVE_FILESYSTEM_ACTION" in codes
    assert all(f["confidence"] == "heuristic" for f in results)

def test_safe_text_does_not_trigger_rules():
    results = scan_security("Review the README and explain the function.")
    assert results == []

def test_valid_skill_has_frontmatter():
    content = """---
name: python-code-reviewer
description: Reviews Python code for bugs and security issues.
---

# Python Code Reviewer

Review the supplied code and report actionable findings.
"""

    result = validate_skill(content)

    assert result["valid"] is True
    assert result["metadata"]["name"] == "python-code-reviewer"


def test_missing_frontmatter_is_rejected():
    content = """name: python-code-reviewer
description: Reviews Python code.

# Objective

Review code.
"""

    result = validate_skill(content)

    assert result["valid"] is False

    assert any(
        finding["code"] == "FRONTMATTER_ERROR"
        for finding in result["findings"]
    )


def test_invalid_name_is_rejected():
    content = """---
name: Python Code Reviewer
description: Reviews Python code.
---

# Objective

Review code.
"""

    result = validate_skill(content)

    assert result["valid"] is False

    assert any(
        finding["code"] == "INVALID_NAME"
        for finding in result["findings"]
    )


def test_markdown_code_fence_is_removed():
    raw = """```markdown
---
name: python-code-reviewer
description: Reviews Python code.
---

# Objective

Review code.
```"""

    cleaned = clean_model_markdown(raw)

    assert cleaned.startswith("---")
    assert not cleaned.startswith("```")
    assert not cleaned.endswith("```")


def test_security_scan_reports_line_number():
    content = """---
name: command-reviewer
description: Reviews command execution.
---

# Security

subprocess.run(command)
"""

    findings = scan_security(content)

    shell_finding = next(
        finding
        for finding in findings
        if finding["code"] == "SHELL_EXECUTION"
    )

    assert shell_finding["line"] == "8"
    assert shell_finding["confidence"] == "heuristic"


def test_security_scan_does_not_execute_content():
    content = """---
name: python-code-reviewer
description: Reviews Python code.
---

# Security

Review code that uses eval() or exec().
"""

    # The scanner only analyzes text; it never evaluates the content.
    findings = scan_security(content)

    assert isinstance(findings, list)