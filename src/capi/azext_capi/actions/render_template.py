# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains action functions for the az capi extension.
"""

import os
import subprocess
import re

from azure.cli.core.azclierror import RequiredArgumentMissingError
from jinja2 import Environment, PackageLoader, StrictUndefined
from jinja2.exceptions import UndefinedError

from azext_capi.helpers.network import urlretrieve
from azext_capi.helpers.generic import match_output
from azext_capi.helpers.os import set_environment_variables
from azext_capi.helpers.run_command import run_shell_command
from azext_capi.helpers.logger import logger


def render_custom_cluster_template(template, filename, args=None):
    """
    Fetch a user-defined template and process it with "clusterctl generate"
    """
    set_environment_variables(args)
    command = ["clusterctl", "generate", "yaml", "--from"]
    if not os.path.isfile(template):
        reg = r"github.com\/[^\/]+?\/[^\/]+?\/blob\/[^\/]+\/[^\/]+?$"
        if not match_output(template, reg):
            file_name = f"raw-{filename}"
            urlretrieve(template, file_name)
            template = file_name
    command += [template]
    try:
        return run_shell_command(command)
    except subprocess.CalledProcessError as err:
        err_command_list = err.args[1]
        err_command_name = err_command_list[0]
        if err_command_name == "clusterctl":
            error_variables = re.search(r"(?<=\[).+?(?=\])", err.stdout)[0]
            msg = "Could not generate workload cluster configuration."
            msg += f"\nPlease set the following environment variables:\n{error_variables}"
        raise RequiredArgumentMissingError(msg) from err


def render_builtin_jinja_template(args):
    """
    Use the built-in template and process it with Jinja
    """
    env = Environment(loader=PackageLoader("azext_capi", "templates"),
                      auto_reload=False, undefined=StrictUndefined)
    logger.debug("Available templates: %s", env.list_templates())
    jinja_template = env.get_template("base.jinja")
    try:
        return jinja_template.render(args)
    except UndefinedError as err:
        msg = f"Could not generate workload cluster configuration.\n{err}"
        raise RequiredArgumentMissingError(msg) from err
