# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

from .run_command import run_shell_command


def generate_jwks_document(public_key):
    """
    Generates JWKS document via AZWI CLI tool
    Returns JWKS filename
    """
    jwks = "jwks.json"
    command = ["azwi", "jwks", "--public-keys", public_key, "--output-file", jwks]
    run_shell_command(command)
    return jwks
