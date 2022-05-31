# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains action functions for the az capi extension.
"""


import json
import os

from azure.cli.core.azclierror import UnclassifiedUserFault

from azext_capi.helpers.azure_resources import create_azure_blob_storage_account, upload_storage_blob
from azext_capi.helpers.azwi import generate_jwks_document
from azext_capi.helpers.keys import generate_key_pair
from azext_capi.helpers.binary import check_azwi
from azext_capi.helpers.os import write_to_file, delete_file
from azext_capi.helpers.network import get_json_from_url
from azext_capi.helpers.generic import get_random_hex_from_bytes
from azext_capi.helpers.run_command import run_shell_command
from azext_capi.actions.render_template import render_custom_cluster_template
from azext_capi.helpers.constants import AZURE_STORAGE_CONTAINER, AZURE_STORAGE_ACCOUNT, KIND_AAD_WORKLOAD_IDENTITY_CONFIG


def create_oidc_issuer_blob_storage_account(cmd, location):
    check_azwi(cmd, install=True)
    key_name = "sa"
    generate_key_pair(key_name)
    rand = get_random_hex_from_bytes()
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

    kind_aad_workload_identity_config = "kind_aad_workload_identity_config.yaml"
    raw_kind_aad_workload_identity_config = f"raw-{kind_aad_workload_identity_config}"
    write_to_file(raw_kind_aad_workload_identity_config, KIND_AAD_WORKLOAD_IDENTITY_CONFIG)
    args = {
        "SERVICE_ACCOUNT_ISSUER": openid_configuration["issuer"],
        "SERVICE_ACCOUNT_KEY_FILE": os.path.realpath(f"{key_name}.pub"),
        "SERVICE_ACCOUNT_SIGNING_KEY_FILE": os.path.realpath(f"{key_name}.key")
    }
    render_template = render_custom_cluster_template(raw_kind_aad_workload_identity_config,
                                                     kind_aad_workload_identity_config, args=args)
    write_to_file(kind_aad_workload_identity_config, render_template)
    return kind_aad_workload_identity_config


def install_mutating_admission_webhook():
    filename = "azure-wi-webhook.yaml"
    url = "https://github.com/Azure/azure-workload-identity/releases/download/v0.10.0/azure-wi-webhook.yaml"
    webhook_template = render_custom_cluster_template(url, filename)
    write_to_file(filename, webhook_template)
    command = ["kubectl", "apply", "-f", filename]
    exception = UnclassifiedUserFault("Could not deploy mutating admission webhook")
    run_shell_command(command, exception)
