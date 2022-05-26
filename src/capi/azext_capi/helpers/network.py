# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This module contains helper functions for the az capi extension.
"""
from urllib.parse import urlparse
import platform
import ssl
import sys
import requests


from six.moves.urllib.request import urlopen

from azure.core.exceptions import HttpResponseError
from azure.cli.core.util import in_cloud_console


def ssl_context():
    """Returns an SSL context appropriate for the python version and environment."""
    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == "Windows"):
        try:
            # added in python 2.7.13 and 3.6
            return ssl.SSLContext(ssl.PROTOCOL_TLS)
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def urlretrieve(url, filename):
    """Retrieves the contents of a URL to a file."""
    print(filename)
    req = urlopen(url, context=ssl_context())  # pylint: disable=consider-using-with
    with open(filename, "wb") as out:
        out.write(req.read())


def get_url_domain_name(url):
    domain = urlparse(url).netloc
    return domain if domain else None


def urlretrieve_tar_package(url, package_name):
    """Retrieves TAR pacakge from URL."""
    response = requests.get(url, stream=True)
    if not response.ok:
        raise HttpResponseError(f"Couldn't retrieve {package_name}")
    with open(package_name, 'wb') as f:
        f.write(response.raw.read())
