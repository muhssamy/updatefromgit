
[![UpdateFromGit PyPI and TestPyPI](https://github.com/muhssamy/updatefromgit/actions/workflows/github-release.yml/badge.svg)](https://github.com/muhssamy/updatefromgit/actions/workflows/github-release.yml)

# Update From Git

This package is built on top of this [repository](https://github.com/PowerBiDevCamp/FabConWorkshopSweden).I have enhanced it to be more suitable for Azure Pipelines.

## Description

This package is designed to be used within an Azure DevOps Pipeline to update a Fabric Workspace from a Git repository using a user with an email and password. It supports both public client and confidential client applications. For more information about the differences, click [here](https://learn.microsoft.com/en-us/entra/msal/msal-client-applications)

**Note** This is currently the only available method because Microsoft does not support service principals for these operations. Once it becomes available, please use it. For more information, check Microsoft Entra supported identities [here](https://learn.microsoft.com/en-us/rest/api/fabric/core/git/update-from-git).

Another method is to schedule a notebook on Fabric running under the authority of a user who is a contributor or higher in an administration workspace using [this](https://semantic-link-labs.readthedocs.io/en/stable/sempy_labs.html#sempy_labs.update_from_git) libirary.

### Install

To install the package, use the following command:

```python
pip install updatefromgit
```

### Usage

First, import the required functions. This example uses a `confidential App` but you can use a public one and omit the `client secret`

```python
import logging
import os
import sys
import time
from azlog import AzLogger

from updatefromgit import (
    acquire_token_user_id_password_confidential,
    commit_all_items_to_git,
    get_git_status,
    update_workspace_from_git,
)

logger = AzLogger(__name__)
logger.setLevel(logging.INFO)

```

Next, create your constants:

```python
FABRIC_API_URL = "https://api.fabric.microsoft.com/v1"
CLIENT_ID = ""
TENANT_ID = ""
USERNAME = ""
PASSWORD = ""
WORKSPACE_ID = ""

```

Then, you can call the functions:

```python
access_token = acquire_token_user_id_password_confidential(
    TENANT_ID, CLIENT_ID, USERNAME, PASSWORD, CLIENT_SECRET
)
update_workspace_from_git(WORKSPACE_ID, access_token)
time.sleep(600) #adjust it per your need
workspace_head = get_git_status(WORKSPACE_ID, access_token)
commit_all_items_to_git(WORKSPACE_ID, workspace_head, access_token)
logger.command("Program Completed")

```

### To edit pipeline connection while migrating the code between dev --> Uat --> Prod

you can use `update_linked_services` 
the following refer to the full code of update from git

```yml
trigger:
  branches:
    include:
      - dev  # Change this to your development branch if different

pr:
  branches:
    include:
      - uat  # Trigger on PRs to UAT

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: AzureKeyVault@2
  displayName: 'Azure Key Vault: da-dev-uaen-01-kv'
  inputs:
    azureSubscription: FabricSPNConnection
    KeyVaultName: 'da-dev-uaen-01-kv'
    SecretsFilter: 'CLIENTID, TENANTID, email, password, CLIENTSECRET'
    RunAsPreJob: true

- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.x'
    addToPath: true

- bash: 'python -m pip install updatefromgit --no-cache-dir --upgrade'
  displayName: 'Bash Script'

- script: |
    python3 -c "from update import update_linked_services; update_linked_services('$(Build.SourcesDirectory)/linkedservice-config.json', '$(Build.SourcesDirectory)')"
  displayName: 'Run Python Script to Modify JSON Files'

- task: Bash@3
  inputs:
    targetType: 'inline'
    script: |
      # Set up Git configuration for committing changes
      git config --global user.email "your-email@example.com"
      git config --global user.name "Your Name"

      # Checkout the UAT branch
      git checkout uat

      # Stage all changes
      git add "$BUILD_SOURCESDIRECTORY/**/*.json"  # Adjust this pattern to your needs

      # Commit changes
      git commit -m "Automated update of pipeline-content.json files from PR"

      # Push changes to the UAT branch
      git push https://$(System.AccessToken)@dev.azure.com/your_org/your_project/_git/your_repo uat

- task: PythonScript@0
  displayName: 'Run a Python script'
  inputs:
    scriptSource: 'filePath'
    scriptPath: '$(Build.SourcesDirectory)/update.py' #look to examples
    arguments: '--WORKSPACE_ID $(WORKSPACE_ID) --CLIENT_ID $(CLIENTID) --TENANT_ID $(TENANTID) --USER_NAME $(email) --PASSWORD $(password) --CLIENT_SECRET $(CLIENTSECRET)'
    workingDirectory: '$(Build.SourcesDirectory)'

```
