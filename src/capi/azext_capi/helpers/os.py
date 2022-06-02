# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

import os
import tarfile


def set_environment_variables(dic=None):
    """
    Sets the key and value items of a dictionary into environment variables.
    """
    if not dic:
        return
    for key, value in dic.items():
        if value:
            os.environ[key] = f"{value}"


def write_to_file(filename, file_input):
    """
    Writes file_input into file
    """
    with open(filename, "w", encoding="utf-8") as manifest_file:
        manifest_file.write(file_input)


def delete_file(file):
    """
    Delete a file from file system
    """
    os.remove(file)


def extract_binary_from_tar_package(binary_path, binary_name, extraction_dir, cleanup=False):
    """
    Extract a binary from tar.gz package.
    Arguments:
    cleanup will delete tar.gz after binary is extracted.
    """
    with tarfile.open(binary_path) as tar:
        tar.extract(binary_name, extraction_dir)

    if cleanup:
        delete_file(binary_path)

    return True


def write_bites_to_file(filename, file_input):
    """
    Write bites input to file.
    """
    with open(filename, "wb") as manifest_file:
        manifest_file.write(file_input)
