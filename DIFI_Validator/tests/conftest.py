# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

#import logging
#import os
#from typing import Any, Dict, List

import pytest

##import urllib3
# pylint: disable=no-name-in-module,import-error,wrong-import-order
#from _pytest.assertion import truncate
#from py.xml import html  # type: ignore

pytest_plugins = []

@pytest.fixture
def ipaddress(request):
    return request.config.getoption("--ipaddress")

def pytest_addoption(parser):
    # add pytest "global" variables so they can be accessed by test fixtures

    # custom options
    parser.addoption("--ipaddress", action="store", help="specify the ipAddress of the DIFI checker",default="1.2.3.4")
