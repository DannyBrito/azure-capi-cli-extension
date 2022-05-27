# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

import json
import subprocess
import os

from azext_capi.helpers.azwi import generate_jwks_document
from azext_capi.helpers.keys import generate_key_pair
from azext_capi.helpers.binary import check_azwi
from azext_capi.helpers.network import get_json_from_url

from Crypto import Random
from knack.prompting import prompt_y_n
from azure.cli.core.azclierror import UnclassifiedUserFault

from .run_command import try_command_with_spinner, run_shell_command
from .constants import AZURE_STORAGE_CONTAINER, AZURE_STORAGE_ACCOUNT
from .os import delete_file


def write_to_file(filename, file_input):
    with open(filename, "w", encoding="utf-8") as manifest_file:
        manifest_file.write(file_input)


def create_resource_group(cmd, rg_name, location, no_logging=False, yes=False):
    msg = f'Create the Azure resource group "{rg_name}" in location "{location}"?'
    if yes or prompt_y_n(msg, default="n"):
        command = ["az", "group", "create", "-l", location, "-n", rg_name]
        if no_logging:
            run_shell_command(command)
        else:
            begin_msg = f"Creating Resource Group: {rg_name}"
            end_msg = f"✓ Created Resource Group: {rg_name}"
            err_msg = f"Could not create resource group {rg_name}"
            try_command_with_spinner(cmd, command, begin_msg, end_msg, err_msg)
        return True
    return False


def delete_resource_group(cmd, resource_group, no_logging=False, yes=False):
    msg = f'Do you want to delete "{resource_group} resource group"?'
    if yes or prompt_y_n(msg, default="n"):
        command = ["az", "group", "delete", "--name", resource_group, "--yes"]
        if no_logging:
            run_shell_command(command)
        else:
            begin_msg = f"Deleting {resource_group} resource group"
            end_msg = f"✓ Deleted {resource_group} resource group"
            error_msg = "Could not delete resource group"
            try_command_with_spinner(cmd, command, begin_msg, end_msg, error_msg)
        return True
    return False


def create_storage_account(account_name, resource_group):
    command = ["az", "storage", "account", "create", "-g", resource_group, "-n", account_name]
    exception = UnclassifiedUserFault("Couldn't create Azure Storage Account!")
    run_shell_command(command, exception)


def create_storage_contanier(container_name, account):
    command = ["az", "storage", "container", "create", "-n", container_name,
               "--public-access", "container", "--account-name", account]
    exception = UnclassifiedUserFault("Couldn't create Azure Storage Container!")
    run_shell_command(command, exception)


def create_azure_blob_storage_account(resource_group, location, storage_account, storage_container):
    try:
        create_resource_group(None, resource_group, location, no_logging=True, yes=True)
    except subprocess.CalledProcessError as err:
        raise UnclassifiedUserFault(f"Couldn't create {resource_group} Resource Group") from err

    create_storage_account(storage_account, resource_group)
    create_storage_contanier(storage_container, storage_account)


def upload_storage_blob(blob_name, container, file):
    command = ["az", "storage", "blob", "upload", "--container-name", container, "--file", file, "--name", blob_name]
    exception = UnclassifiedUserFault(f"Couldn't upload {blob_name} blob to {container}")
    run_shell_command(command, exception)


def create_oidc_issuer_blob_storage_account(cmd, location):
    check_azwi(cmd, install=True)
    key_name = "sa"
    generate_key_pair(key_name)

    rand = Random.get_random_bytes(4).hex()
    storage_account = f"oidcissuer{rand}"
    resource_group = "oidc-issuer"
    storage_container = "oidc-test"
    os.environ[AZURE_STORAGE_ACCOUNT] = storage_account
    os.environ[AZURE_STORAGE_CONTAINER] = storage_container
    create_azure_blob_storage_account(resource_group, location, storage_account, storage_container)

    openid_configuration = {
        "issuer": f"https://{storage_account}.blob.core.windows.net/{storage_container}/",
        "jwks_uri": f"https://{storage_account}.blob.core.windows.net/{storage_container}/openid/v1/jwks",
        "response_types_supported": ["id_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"]
    }

    openid_file = "openid_configuration.json"
    write_to_file(openid_file, json.dumps(openid_configuration))

    blob_name = ".well-known/openid-configuration"
    upload_storage_blob(blob_name, storage_container, openid_file)

    delete_file(openid_file)

    url = openid_configuration["issuer"] + blob_name
    req = get_json_from_url(url, error_msg="Could not retreive Discory document")
    if req != openid_configuration:
        raise UnclassifiedUserFault("Discory document is not publicly accessible")

    jwks = generate_jwks_document(f"{key_name}.pub")
    blob_name = "openid/v1/jwks"
    upload_storage_blob(blob_name, storage_container, jwks)

    url = openid_configuration["issuer"] + blob_name
    req = get_json_from_url(url, error_msg="Could not retreive JWKS document")
    if "keys" not in req:
        raise UnclassifiedUserFault("JWKS document is not publicly accessible")
