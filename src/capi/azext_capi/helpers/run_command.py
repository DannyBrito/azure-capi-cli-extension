# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess

from azure.cli.core.azclierror import UnclassifiedUserFault

from .spinner import Spinner
from .logger import logger, is_verbose


def run_shell_command(command, exception=None):
    """
    Simulates Running a CLI command via subproccess module.
    Args:
    exception: custom exception to be raised if command fails
    """
    # if --verbose, don't capture stderr
    stderr = None if is_verbose() else subprocess.STDOUT
    try:
        output = subprocess.check_output(command, universal_newlines=True, stderr=stderr)
        logger.info("%s returned:\n%s", " ".join(command), output)
        return output
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        if exception is not None:
            raise exception from err
        raise


def try_command_with_spinner(cmd, command, spinner_begin_msg, spinner_end_msg,
                             error_msg, include_error_stdout=False):
    with Spinner(cmd, spinner_begin_msg, spinner_end_msg):
        try:
            run_shell_command(command)
        except (subprocess.CalledProcessError, FileNotFoundError) as err:
            if include_error_stdout:
                error_msg += f"\n{err.stdout}"
            raise UnclassifiedUserFault(error_msg) from err
