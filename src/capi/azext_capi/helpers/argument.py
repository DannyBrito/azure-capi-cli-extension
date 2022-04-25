# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=missing-docstring

import os

from azure.cli.core import get_default_cli


# Setting default values, highest -> lowest
# Hierarchy: value in parameter -> env variable -> config value -> static value
def get_default_arg_from_config(arg_name, fallback):
    config = get_default_cli().config
    return config.get("capi", arg_name, fallback)


def get_default_arg(arg_name):
    """
    Hierarchy: passed argument value -> env variable -> config value -> static value
    """
    allowed_defaults_values = {
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
    if arg_name in allowed_defaults_values:
        return get_default_arg_from_config(arg_name, allowed_defaults_values[arg_name])
    raise NoAllowedGetDefaultArgument(f"{arg_name} argument doesn't have an allowed default value")


class NoAllowedGetDefaultArgument(Exception):

    def __init__(self, message="No allowed to get defaul argument value") -> None:
        self.message = message
        super().__init__()
