# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""

from knack.prompting import prompt_y_n
from azure.cli.core.azclierror import UnclassifiedUserFault

from .run_command import try_command_with_spinner, run_shell_command


def create_resource_group(cmd, rg_name, location, no_logging=False, yes=False):
    """
    Create an Azure Resource Group
    """
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
    """
    Deletes an Azure Resource Group
    """
    msg = f'Do you want to delete "{resource_group} resource group"?'
    if yes or prompt_y_n(msg, default="n"):
        command = ["az", "group", "delete", "--name", resource_group, "--yes"]
        if no_logging:
            exception = UnclassifiedUserFault(f"Couldn't create {resource_group} Resource Group")
            run_shell_command(command, exception)
        else:
            begin_msg = f"Deleting {resource_group} resource group"
            end_msg = f"✓ Deleted {resource_group} resource group"
            error_msg = "Could not delete resource group"
            try_command_with_spinner(cmd, command, begin_msg, end_msg, error_msg)
        return True
    return False


def create_storage_account(account_name, resource_group):
    """
    Creates an Azure Storage Account
    """
    command = ["az", "storage", "account", "create", "-g", resource_group, "-n", account_name]
    exception = UnclassifiedUserFault("Couldn't create Azure Storage Account!")
    run_shell_command(command, exception)


def create_storage_contanier(container_name, account):
    """
    Creates an Azure Storage Container
    """
    command = ["az", "storage", "container", "create", "-n", container_name,
               "--public-access", "container", "--account-name", account]
    exception = UnclassifiedUserFault("Couldn't create Azure Storage Container!")
    run_shell_command(command, exception)


def create_azure_blob_storage_account(resource_group, location, storage_account, storage_container):
    """
    Creates all required resources for a blob storage account:
    1. Creates Resource Group
    2. Creates Storage Account
    3. Creates Storage Container
    """
    create_resource_group(None, resource_group, location, no_logging=True, yes=True)
    create_storage_account(storage_account, resource_group)
    create_storage_contanier(storage_container, storage_account)


def upload_storage_blob(blob_name, container, file):
    """
    Uploads File as a blob into Storage Container
    """
    command = ["az", "storage", "blob", "upload", "--container-name", container, "--file", file, "--name", blob_name]
    exception = UnclassifiedUserFault(f"Couldn't upload {blob_name} blob to {container}")
    run_shell_command(command, exception)


def create_azure_key_vault(keyvault_name, resource_group, location):
    """
    Create Azure Keyvault
    """
    command = ["az", "keyvault", "create", "--name", keyvault_name, "--location", location,
               "--resource-group", resource_group]
    exception = UnclassifiedUserFault(f"Could not create {keyvault_name} keyvault")
    run_shell_command(command, exception)


def create_azure_keyvault_secret(secret, keyvault_secret_name, keyvault_name):
    """
    Create Azure Keyvault Secret
    """
    command = ["az", "keyvault", "secret", "set", "--vault-name", keyvault_name,
               "--name", keyvault_secret_name, "--value", secret]
    exception = UnclassifiedUserFault(f"Could not create {keyvault_secret_name} secret")
    run_shell_command(command, exception)


def create_azure_key_vault_and_secret(resource_group, location, keyvault_name, keyvault_secret_name, secret):
    """
    Create Azure Keyvault and Secret
    """
    create_resource_group(None, resource_group, location, no_logging=True, yes=True)
    create_azure_key_vault(keyvault_name, resource_group, location)
    create_azure_keyvault_secret(secret, keyvault_secret_name, keyvault_name)
