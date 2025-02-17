# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

import re


def has_kind_prefix(inpt_str):
    """Returns bool if input has 'kind-' prefix"""
    return inpt_str.startswith("kind-")


def match_output(output, regexp=None):
    """Returns regex search result against given parameter"""
    return re.search(regexp, output) if regexp is not None else None
