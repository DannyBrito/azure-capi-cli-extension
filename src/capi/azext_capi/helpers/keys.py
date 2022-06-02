# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

from Crypto.PublicKey import RSA

from azext_capi.helpers.os import write_bites_to_file


def generate_key_pair(key_name):
    """
    Generates public and private pair keys
    """
    key = RSA.generate(2048)
    private_key = key.export_key("PEM")
    public_key = key.public_key().export_key("PEM")
    write_bites_to_file(f"{key_name}.key", private_key)
    write_bites_to_file(f"{key_name}.pub", public_key)
