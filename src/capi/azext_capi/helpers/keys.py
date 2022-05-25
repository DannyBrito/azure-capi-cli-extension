# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

from Crypto.PublicKey import RSA


# Temporal till custom template PR merge its a copy same method
def write_bites_to_file(filename, file_input):
    """
    Write bites input to file.
    """
    with open(filename, "wb") as manifest_file:
        manifest_file.write(file_input)


def generate_key_pair(key_name):
    key = RSA.generate(2048)
    private_key = key.export_key("PEM")
    public_key = key.public_key().export_key("PEM")
    write_bites_to_file(f"{key_name}.key", private_key)
    write_bites_to_file(f"{key_name}.pub", public_key)
