# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
import os
import sys
import tempfile
import unittest
from collections import namedtuple
from unittest.mock import patch, Mock

from azure.cli.core.azclierror import UnclassifiedUserFault
from azure.cli.core.azclierror import ResourceNotFoundError

import azext_capi.helpers.network as network
import azext_capi.helpers.generic as generic
from azext_capi.custom import create_resource_group, create_new_management_cluster, get_user_prompt_or_default, management_cluster_components_missing_matching_expressions
from azext_capi.helpers.kubectl import check_kubectl_namespace, find_attribute_in_context, find_kubectl_current_context, find_default_cluster, add_kubeconfig_to_command
from azext_capi.helpers.run_command import try_command_with_spinner, run_shell_command


class TestSSLContextHelper(unittest.TestCase):

    Case = namedtuple('Case', ['major', 'minor', 'cloud_console', 'system'])

    cases = [
        Case(3, 4, False, 'Windows'),
        Case(3, 4, True, 'Windows'),
        Case(3, 4, False, 'Linux'),
        Case(3, 4, True, 'Linux'),
        Case(3, 6, False, 'Windows'),
        Case(3, 6, True, 'Windows'),
        Case(3, 6, False, 'Linux'),
        Case(3, 6, True, 'Linux'),
        Case(3, 9, False, 'Windows'),
        Case(3, 9, True, 'Windows'),
        Case(3, 9, False, 'Linux'),
        Case(3, 9, True, 'Linux'),
    ]

    def test_ssl_context(self):
        for case in self.cases:
            with patch('azure.cli.core.util.in_cloud_console', return_value=case.cloud_console):
                with patch.object(sys, 'version_info', (case.major, case.minor)):
                    with patch('platform.system', return_value=case.system):
                        self.assertTrue(network.ssl_context())


class TestURLRetrieveHelper(unittest.TestCase):

    @patch('azext_capi.helpers.network.urlopen')
    def test_urlretrieve(self, mock_urlopen):
        random_bytes = os.urandom(2048)
        req = mock_urlopen.return_value
        req.read.return_value = random_bytes
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.close()
            network.urlretrieve('https://dummy.url', fp.name)
            self.assertEqual(open(fp.name, 'rb').read(), random_bytes)
            os.unlink(fp.name)


class FindDefaultCluster(unittest.TestCase):

    def setUp(self):
        self.cmd = Mock()
        self.match_output_patch = patch('azext_capi.helpers.kubectl.match_output')
        self.match_output_mock = self.match_output_patch.start()
        self.match_output_mock.return_value = None
        self.addCleanup(self.match_output_patch.stop)

        self.run_shell_command_patch = patch('azext_capi.helpers.kubectl.run_shell_command')
        self.run_shell_command_mock = self.run_shell_command_patch.start()
        self.addCleanup(self.run_shell_command_patch.stop)

    # Test kubernetes cluster is found and running
    def test_found_k8s_cluster_running_state(self):
        self.run_shell_command_mock.return_value = "fake_return"
        self.match_output_mock.return_value = Mock()
        result = find_default_cluster()
        self.match_output_mock.assert_called_once()
        self.assertTrue(result)

    # Test kubernetes cluster is found but not running state matched
    def test_found_cluster_non_running_state(self):
        self.run_shell_command_mock.return_value = "fake_return"
        with self.assertRaises(ResourceNotFoundError):
            find_default_cluster()

    # Test error with command ran
    def test_encouter_error_with_ran_command(self):
        self.run_shell_command_mock.side_effect = subprocess.CalledProcessError(3, ['fakecommand'])
        with self.assertRaises(subprocess.CalledProcessError):
            find_default_cluster()


class CreateNewManagementCluster(unittest.TestCase):

    def setUp(self):
        self.cmd = Mock()
        self.prompt_y_n_patch = patch('azext_capi.custom.prompt_y_n')
        self.prompt_y_n_mock = self.prompt_y_n_patch.start()
        self.addCleanup(self.prompt_y_n_patch.stop)
        self.get_cluster_prompt_patch = patch('azext_capi.custom.get_cluster_name_by_user_prompt')
        self.get_cluster_prompt_mock = self.get_cluster_prompt_patch.start()
        self.addCleanup(self.get_cluster_prompt_patch.stop)
        self.try_cmd_patch = patch('azext_capi.custom.try_command_with_spinner')
        self.try_cmd_mock = self.try_cmd_patch.start()
        self.addCleanup(self.try_cmd_patch.stop)
        self.prompt_list_patch = patch('azext_capi.custom.prompt_choice_list')
        self.prompt_list_mock = self.prompt_list_patch.start()
        self.addCleanup(self.prompt_list_patch.stop)

    # Test exit after user input
    def test_user_choices_exit_option(self):
        self.prompt_list_mock.return_value = 2
        result = create_new_management_cluster(self.cmd)
        self.assertFalse(result)

    # Test create local kind management cluster
    def test_user_choices_kind_option(self):
        self.prompt_list_mock.return_value = 1
        with patch('azext_capi.custom.check_kind'):
            result = create_new_management_cluster(self.cmd)
            self.assertTrue(result)

    # Test create AKS management cluster
    def test_user_choices_aks_option(self):
        self.prompt_list_mock.return_value = 0
        with patch('azext_capi.custom.create_aks_management_cluster'):
            result = create_new_management_cluster(self.cmd)
            self.assertTrue(result)


class RunShellMethod(unittest.TestCase):

    def setUp(self):
        self.command = ["fake-command"]

    # Test run valid command
    @patch('subprocess.check_output')
    def test_run_valid_command(self, check_out_mock):
        run_shell_command(self.command)
        check_out_mock.assert_called_once()

    # Test command is non existing or invalid
    def test_run_invalid_command(self):
        with self.assertRaises(FileNotFoundError):
            run_shell_command(self.command)


class FindKubectlCurrentContext(unittest.TestCase):

    def setUp(self):
        self.context_name = "fake-context"
        self.run_shell_patch = patch('azext_capi.helpers.kubectl.run_shell_command')
        self.run_shell_mock = self.run_shell_patch.start()
        self.run_shell_mock.return_value = None
        self.addCleanup(self.run_shell_patch.stop)

    # Test found current context
    def test_existing_current_context(self):
        self.run_shell_mock.return_value = self.context_name
        result = find_kubectl_current_context()
        self.assertEquals(result, self.context_name)

    # Test found current context with extra space
    def test_return_value_is_sanitized(self):
        self.run_shell_mock.return_value = f"  {self.context_name}  "
        result = find_kubectl_current_context()
        self.assertEquals(result, self.context_name)

    # Test does not found current context
    def test_no_found_current_context(self):
        self.run_shell_mock.return_value = None
        error = subprocess.CalledProcessError(3, ['fakecommand'], output="current-context is not set")
        self.run_shell_mock.side_effect = error
        result = find_kubectl_current_context()
        self.assertIsNone(result)


class FindAttributeInContext(unittest.TestCase):

    def setUp(self):
        self.context_name = "context-name-fake"
        self.run_shell_patch = patch('azext_capi.helpers.kubectl.run_shell_command')
        self.run_shell_mock = self.run_shell_patch.start()
        self.run_shell_mock.return_value = None
        self.addCleanup(self.run_shell_patch.stop)

    # Test found cluster in context
    def test_existing_context(self):
        cluster_name = "cluster-name-fake"
        context_info = f"* {self.context_name} {cluster_name}"
        self.run_shell_mock.return_value = context_info
        result = find_attribute_in_context(self.context_name, "cluster")
        self.assertEquals(result, cluster_name)

    # Test does not found context
    def test_no_existing_context(self):
        self.run_shell_mock.return_value = None
        self.run_shell_mock.side_effect = subprocess.CalledProcessError(3, ['fakecommand'])
        result = find_attribute_in_context(self.context_name, "cluster")
        self.assertIsNone(result)


class CreateResourceGroup(unittest.TestCase):

    def setUp(self):
        self.cmd = Mock()
        self.group = "fake-resource-group"
        self.location = "fake-location"
        self.try_command_patch = patch('azext_capi.custom.try_command_with_spinner')
        self.try_command_mock = self.try_command_patch.start()
        self.try_command_mock.return_value = None
        self.addCleanup(self.try_command_patch.stop)

    # Test created new resource group
    def test_create_valid_resource_group(self):
        result = create_resource_group(self.cmd, self.group, self.location, True)
        self.assertTrue(result)

    # Test error creating resource group
    def test_raise_error_invalid_resource_group(self):
        self.try_command_mock.side_effect = subprocess.CalledProcessError(3, ['fakecommand'])
        with self.assertRaises(subprocess.CalledProcessError):
            create_resource_group(self.cmd, self.group, self.location, True)


class GetUserPromptMethodTest(unittest.TestCase):

    def setUp(self):
        self.fake_input = "fake-input"
        self.fake_prompt = Mock()
        self.fake_default_value = Mock()
        self.prompt_method_patch = patch('azext_capi.helpers.prompt.prompt_method')
        self.prompt_method_mock = self.prompt_method_patch.start()
        self.prompt_method_mock.return_value = None
        self.addCleanup(self.prompt_method_patch.stop)

    # Test user input return without any validation
    def test_user_input_without_validation(self):
        prompt_mock = self.prompt_method_mock
        prompt_mock.return_value = self.fake_input
        result = get_user_prompt_or_default(self.fake_prompt, self.fake_default_value)
        self.assertEquals(result, self.fake_input)

    # Test skip-prompt to return default value
    def test_skip_prompt_flag(self):
        prompt_mock = self.prompt_method_mock
        prompt_mock.return_value = None
        result = get_user_prompt_or_default(self.fake_prompt, self.fake_default_value, skip_prompt=True)
        self.assertEquals(result, self.fake_default_value)
        self.assertIsNotNone(result)

    # Test input against validation
    def test_write_user_input_with_validation(self):
        prompt_mock = self.prompt_method_mock
        valid_input = "abcd"
        regex_validator = "^[a-z]+$"
        prompt_mock.side_effect = ["Invalid-input_$(2", valid_input]
        result = get_user_prompt_or_default(self.fake_prompt, self.fake_default_value, regex_validator)
        self.assertEquals(result, valid_input)
        self.assertEquals(prompt_mock.call_count, 2)
        self.assertNotEquals(result, self.fake_default_value)

    # Test invalid user input against validation
    def test_invalid_input_with_validation(self):
        prompt_mock = self.prompt_method_mock
        regex_validator = "^[a-z]+$"
        prompt_mock.side_effect = ["Invalid-input_$(2"]
        with self.assertRaises(StopIteration):
            get_user_prompt_or_default(self.fake_prompt, self.fake_default_value, regex_validator)

    # Test user enter empty input for default value
    def test_user_skips_input_for_default_value(self):
        prompt_mock = self.prompt_method_mock
        empty_input = ""
        prompt_mock.return_value = empty_input
        result = get_user_prompt_or_default(self.fake_prompt, self.fake_default_value)
        self.assertEquals(result, self.fake_default_value)
        self.assertNotEquals(result, empty_input)


class TryCommandWithSpinner(unittest.TestCase):

    def setUp(self):
        self.cmd = Mock()
        self.begin_msg = "begin"
        self.end_msg = "end"
        self.error_msg = "error"
        self.command = ["fake-command"]
        self.spinner_patch = patch('azext_capi.helpers.run_command.Spinner')
        self.spinner_mock = self.spinner_patch.start()
        self.addCleanup(self.spinner_patch.stop)

    # Test valid command run
    def test_command_run(self):
        with patch('subprocess.check_output') as mock:
            try_command_with_spinner(self.cmd, self.command, self.begin_msg,
                                     self.end_msg, self.error_msg)
            mock.assert_called_once()

    # Test invalid command run
    def test_invalid_command_run(self):
        with self.assertRaises(UnclassifiedUserFault) as cm:
            try_command_with_spinner(self.cmd, self.command, self.begin_msg,
                                     self.end_msg, self.error_msg)
        self.assertEquals(cm.exception.error_msg, self.error_msg)


class CheckKubectlNamespaceTest(unittest.TestCase):

    def setUp(self):
        self.namespace = "fake"
        self.command = ["fake-command"]

        self.run_shell_command_patch = patch('azext_capi.helpers.kubectl.run_shell_command')
        self.run_shell_command_mock = self.run_shell_command_patch.start()
        self.addCleanup(self.run_shell_command_patch.stop)

        self.match_output_patch = patch('azext_capi.helpers.kubectl.match_output')
        self.match_output_mock = self.match_output_patch.start()
        self.addCleanup(self.match_output_patch.stop)

    def test_no_existing_namespace(self):
        error_msg = f"namespace: {self.namespace} could not be found!"
        error_side_effect = subprocess.CalledProcessError(2, self.command, output=error_msg)
        self.run_shell_command_mock.side_effect = error_side_effect
        with self.assertRaises(ResourceNotFoundError) as cm:
            check_kubectl_namespace(self.namespace)
        self.assertEquals(cm.exception.error_msg, error_msg)

    def test_no_active_namespace(self):
        self.run_shell_command_mock.return_value = f"{self.namespace} FakeStatus FakeAge"
        self.match_output_mock.return_value = None
        with self.assertRaises(ResourceNotFoundError) as cm:
            check_kubectl_namespace(self.namespace)
        self.assertEquals(cm.exception.error_msg, f"namespace: {self.namespace} status is not Active")

    def test_existing_namespace(self):
        self.run_shell_command_mock.return_value = f"{self.namespace} Active FakeAge"
        self.match_output_mock.return_value = True
        output = check_kubectl_namespace(self.namespace)
        self.assertIsNone(output)


class ManagementClusterComponentsMissingMatchExpressionTest(unittest.TestCase):

    ValidCases = [
        "namespace: fake could not be found",
        "No resources found in fake-ns namespace",
        "No Fake installation found"
    ]

    InvalidCases = [
        "",
        "fake",
        "Invalid",
        "No installation found"
    ]

    def test_valid_matches(self):
        for out in self.ValidCases:
            self.assertTrue(management_cluster_components_missing_matching_expressions(out))

    def test_invalid_matches(self):
        for out in self.InvalidCases:
            self.assertIsNone(management_cluster_components_missing_matching_expressions(out))


class AddKubeconfigFlagMethodTest(unittest.TestCase):

    def test_no_empty_kubeconfig(self):
        fake_kubeconfig = "fake-kubeconfig"
        output = add_kubeconfig_to_command(fake_kubeconfig)
        self.assertEquals(len(output), 2)
        self.assertEquals(output[1], fake_kubeconfig)

    def test_no_kubeconfig_argument(self):
        output = add_kubeconfig_to_command()
        self.assertEquals(len(output), 0)


class HasKindPrefix(unittest.TestCase):

    def test_valid_prefix(self):
        fake_input = "kind-fake"
        self.assertTrue(generic.has_kind_prefix(fake_input))

    def test_no_prefix(self):
        fake_input = "fake"
        self.assertFalse(generic.has_kind_prefix(fake_input))


class GetUrlDomainName(unittest.TestCase):

    def test_correct_url(self):
        fake_url = "https://www.notrealdomain.fake"
        result = network.get_url_domain_name(fake_url)
        self.assertIn(result, fake_url)

    def test_invalid_url(self):
        fake_url = "invalid-url"
        result = network.get_url_domain_name(fake_url)
        self.assertIsNone(result)
