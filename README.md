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
