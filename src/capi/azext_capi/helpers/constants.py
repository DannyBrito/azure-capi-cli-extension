# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

MANAGEMENT_RG_NAME = "MANAGEMENT_RG_NAME"
KUBECONFIG = "KUBECONFIG"

AZURE_STORAGE_ACCOUNT = "AZURE_STORAGE_ACCOUNT"
AZURE_STORAGE_CONTAINER = "AZURE_STORAGE_CONTAINER"

KIND_AAD_WORKLOAD_IDENTITY_CONFIG = """\
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraMounts:
    - hostPath: ${SERVICE_ACCOUNT_KEY_FILE}
      containerPath: /etc/kubernetes/pki/sa.pub
    - hostPath: ${SERVICE_ACCOUNT_SIGNING_KEY_FILE}
      containerPath: /etc/kubernetes/pki/sa.key
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        service-account-issuer: ${SERVICE_ACCOUNT_ISSUER}
        service-account-key-file: /etc/kubernetes/pki/sa.pub
        service-account-signing-key-file: /etc/kubernetes/pki/sa.key
    controllerManager:
      extraArgs:
        service-account-private-key-file: /etc/kubernetes/pki/sa.key
"""
