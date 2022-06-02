# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core import get_default_cli


def get_config_cli():
    """
    Gets config CLI Object
    """
    return get_default_cli().config


# Setting default values, highest -> lowest
# Hierarchy: value in parameter -> env variable -> config value -> static value
def get_default_arg_from_config(arg_name, fallback):
    """
    Gets default capi default argument value
    """
    config = get_config_cli()
    return config.get("capi", arg_name, fallback)


def get_default_arg(arg_name):
    """
    Hierarchy: passed argument value -> env variable -> config value -> static value
    """
    ALLOWED_DEFAULT_ARGUMENTS = {
        "location": None,
        "group": None,
        "control_plane_machine_type": os.environ.get("AZURE_CONTROL_PLANE_MACHINE_TYPE", "Standard_D2s_v3"),
        "control_plane_machine_count": int(os.environ.get("AZURE_CONTROL_PLANE_MACHINE_COUNT", "3")),
        "node_machine_type": os.environ.get("AZURE_NODE_MACHINE_TYPE", "Standard_D2s_v3"),
        "node_machine_count": int(os.environ.get("AZURE_NODE_MACHINE_COUNT", "3")),
        "kubernetes_version": os.environ.get("AZURE_KUBERNETES_VERSION", "1.22.8"),
        "ssh_public_key": os.environ.get("AZURE_SSH_PUBLIC_KEY_B64", ""),
        "vnet_name": None
    }
    if arg_name in ALLOWED_DEFAULT_ARGUMENTS:
        return get_default_arg_from_config(arg_name, ALLOWED_DEFAULT_ARGUMENTS[arg_name])
    raise NoAllowedGetDefaultArgument(f"{arg_name} argument doesn't have an allowed default value")


def get_all_capi_set_defaults():
    """
    Get all set default values in capi section
    """
    config = get_config_cli()
    return config.items("capi")


def delete_capi_default_section():
    """
    Deletes all set default values in capi section
    """
    config = get_config_cli()
    save_capi_config = get_all_capi_set_defaults()
    for item in save_capi_config:
        config.remove_option("capi", item["name"])
    return save_capi_config


def sets_list_in_capi_section(list):
    """
    Deletes all set default values in capi section
    """
    config = get_config_cli()
    for item in list:
        config.set_value("capi", item["name"], item["value"])


class NoAllowedGetDefaultArgument(Exception):

    def __init__(self, message="No allowed to get defaul argument value") -> None:
        self.message = message
        super().__init__()
