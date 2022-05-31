# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

import re
from Crypto import Random


def has_kind_prefix(inpt_str):
    """Returns bool if input has 'kind-' prefix"""
    return inpt_str.startswith("kind-")


def match_output(output, regexp=None):
    """Returns regex search result against given parameter"""
    return re.search(regexp, output) if regexp is not None else None


def get_random_hex_from_bytes(bytes_number=4):
    """Returns random hex from number of radomn bytes"""
    return Random.get_random_bytes(bytes_number).hex()
