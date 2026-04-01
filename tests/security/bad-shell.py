# DELIBERATELY VULNERABLE — test fixture for pre-commit hook validation
# This file should be BLOCKED by security hooks.

import subprocess


def run_user_command(cmd):
    """Shell injection vulnerability: user-controlled string passed to shell."""
    subprocess.call(cmd, shell=True)
