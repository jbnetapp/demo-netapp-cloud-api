## demo NetApp cloud API
This a simple NetApp Cloud API. The script cloudsync.py is a simple Python script to show how to work with cloudsync. 

**WARNING** Never used this script on production system the aim is only for LAB and Demo

The script need to be used with **python 3**

The folowing python modules must be installed (windows):
```
pip install ssl
pip install json
pip install OpenSSL 
pip insatll urllib3
pip install requests
```
The folowing python modules must be installed (Linux):
```
python3 -m pip install pyopenssl
python3 -m pip insatll urllib3
python3 -m pip install requests
```

# Setup the script
## Create API configuratoin File with your NetApp Cloud Central Credential

The configuration file **api.conf** must be store on the following directory base on your operating system:
- On Linux the File must be save on **$HOME/NetAppCloud/api.conf**
- On Windows the File must be save on **%homedrive%\%homepath%\NetAppCloud\api.conf**

The configuration file **api.conf** must containt the following two section header:
- [DEFAULT] to store default value
- [API-LOGIN] to store you NetApp cloud Login information

NetApp Cloud Central Services use OAuth 2.0, an industry-standard protocol, for authorization. Communicating with an authenticated endpoint is a two step-process 
- Acquire a JWT access token from the OAuth token endpoint.
- Call an API endpoint with the JWT access token. 

NetApp Cloud Central users can be:
- Federated users (Active-Directory). 
    - If your user is federated, you must use a **refresh token Access** to Acquire a JWT **access token** from the OAuth token endpoint.
    - To get your **refresh token Access** login to the https://services.cloud.netapp.com/refresh-token 
        - Click on **Generate Refresh Token** or click on **Revoke Token(s)** 
        - <img src="Pictures/Refresh-Token-Generator.png" alt="NetApp Refresh Token" width="1100" height="350">
    - Create the Configuration File for federated users: 
        ```
        #  cat $HOME/NetAppCloud/api.conf
        [DEFAULT]
        version = 1
        update = 1

        [API_LOGIN]
        grant_type = refresh_token
        refresh_token = <YOUR_REFRESH_TOKEN_ACCESS>
        client_id = Mu0V1ywgYteI6w1MbD15fKfVIUrNXGWC
        ```

- Non-Federated users (Regular Access) you need to create username and password input in the configuration file
    - Create the configuration file for Regular Access:
        ```
        #  cat $HOME/NetAppCloud/api.conf
        [API_LOGIN]
        grant_type = password
        username = <YOUR EMAIL NETAPP CLOUD CENTRAL>
        password = <YOUR PASSWORD >
        audience = https://api.cloud.netapp.com
        client_id = QC3AgHk6qdbmC7Yyr82ApBwaaJLwRrNO        
        ```

## Get the JWT access token  
When the configuration file contain user information the script can get your **JWT access token** and it will be automatically saved in your configuration file in a new section header [API_TOKEN]

Get the **JWT access token** :
```
# python3 cloudsync.py --account-list
```



# Use the script
Display help
```
 python3 cloudsync.py --help
usage: cloudsync.py [-h] [-d] [--account-id ACCOUNT_ID]
                    (--account-list | --create-relation CREATE_RELATION_FILE | --delete-relation DELETE_RELATION_ID | --sync-relation SYNC_RELATION_ID | --print-relations)

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           select debug mode
  --account-id ACCOUNT_ID
                        select the cloudmanager account name: ACCOUNT_NAME
  --account-list        print cloudsnyc accounts
  --create-relation CREATE_RELATION_FILE
                        create a new cloudsync relation from Json CREATE_RELATION_FILE
  --delete-relation DELETE_RELATION_ID
                        delete the cloudsync relation with id DELETE_RELATION_ID
  --sync-relation SYNC_RELATION_ID
                        sync the cloudsync relation with id SYNC_RELATION_ID
  --print-relations     print cloudsnyc relations
```

Display NetApp Account list associate with your NetApp Central user
```
# python3 cloudsync.py --account-list
Print NetApp Account list:
Blanchet account_id: [account-yX7cS8vU]
Demo_SIM account_id: [account-j3aZttuL]
NetAppHCL account_id: [account-U0dbRcKS]
```

Print CloudSync Relations list
```
# python3 cloudsync.py --account-id account-U0dbRcKS --print
Print cloudsync relations:

id: 61c2e054b10e1f362ede48e1
account: 5e528f4504a9a4d63d6962de
dataBroker: 616d9c8d48301b1e6cdfe1df
source: {'protocol': 'azure', 'azure': {'storageAccountName': 'jbdemostorageaccount', 'container': 'jbblob', 'prefix': 'DIR1', 'tags': [], 'provider': 'azure'}}
target: {'protocol': 'azure', 'azure': {'storageAccountName': 'jbdemostorageaccount', 'container': 'jbblobcopy', 'prefix': '', 'tags': [], 'blobTier': 'HOT', 'provider': 'azure'}}
type: Sync
status: DONE

```

Sync a CloudSync Relation 
```
# python3 cloudsync.py --account-id account-U0dbRcKS --sync 61c2e054b10e1f362ede48e1
Sync cloudsync relation ID: 61c2e054b10e1f362ede48e1

```

The relation is in RUNNING state
```
# python3 cloudsync.py --account-id account-U0dbRcKS --print
Print cloudsync relations:

id: 61c2e054b10e1f362ede48e1
account: 5e528f4504a9a4d63d6962de
dataBroker: 616d9c8d48301b1e6cdfe1df
source: {'protocol': 'azure', 'azure': {'storageAccountName': 'jbdemostorageaccount', 'container': 'jbblob', 'prefix': 'DIR1', 'tags': [], 'provider': 'azure'}}
target: {'protocol': 'azure', 'azure': {'storageAccountName': 'jbdemostorageaccount', 'container': 'jbblobcopy', 'prefix': '', 'tags': [], 'blobTier': 'HOT', 'provider': 'azure'}}
type: Sync
status: RUNNING
```

if we Sync the Relation during a sync the script display the error message report return by cloudsync sync request: 
```
# python3 cloudsync.py --account-id account-U0dbRcKS --sync 61c2e054b10e1f362ede48e1
Sync cloudsync relation ID: 61c2e054b10e1f362ede48e1
ERROR: {"code":400,"message":"A sync action is running right now, can not run another action"}
```

Delete a CloudSync relation
```
# python3 cloudsync.py --account-id account-U0dbRcKS --delete 61c2e054b10e1f362ede48e1 -d
Delete cloudsync relation ID: 61c2e054b10e1f362ede48e1
```

Debug:
```
# python3 cloudsync.py --account-id account-U0dbRcKS --account-list --debug
DEBUG: [DEFAULT: <Section: DEFAULT> ]
DEBUG: [API_LOGIN: <Section: API_LOGIN> ]
DEBUG: [API_TOKEN: <Section: API_TOKEN> ]
DEBUG: [API Configuration File: /home/blanchet/NetAppCloud/api.conf]
DEBUG: [access_token: ******************************************************************************************]
DEBUG: [url: https://api.cloudsync.netapp.com/api/accounts ]
DEBUG: [status_code: 200]
DEBUG: [text: [{"accountId":"account-yX7cS8vU","name":"Blanchet"},{"accountId":"account-j3aZttuL","name":"Demo_SIM"},{"accountId":"account-U0dbRcKS","name":"NetAppHCL"}]]
DEBUG: [content: b'[{"accountId":"account-yX7cS8vU","name":"Blanchet"},{"accountId":"account-j3aZttuL","name":"Demo_SIM"},{"accountId":"account-U0dbRcKS","name":"NetAppHCL"}]']
DEBUG: [reason: OK]
DEBUG: [access_token : *****************************************************************************************]
Print NetApp Account list:
DEBUG: [url: https://api.cloudsync.netapp.com/api/accounts ]
DEBUG: [status_code: 200]
DEBUG: [text: [{"accountId":"account-yX7cS8vU","name":"Blanchet"},{"accountId":"account-j3aZttuL","name":"Demo_SIM"},{"accountId":"account-U0dbRcKS","name":"NetAppHCL"}]]
DEBUG: [content: b'[{"accountId":"account-yX7cS8vU","name":"Blanchet"},{"accountId":"account-j3aZttuL","name":"Demo_SIM"},{"accountId":"account-U0dbRcKS","name":"NetAppHCL"}]']
DEBUG: [reason: OK]
DEBUG: [{'status': 'success', 'message': 'ok', 'accounts': '[{"accountId":"account-yX7cS8vU","name":"Blanchet"},{"accountId":"account-j3aZttuL","name":"Demo_SIM"},{"accountId":"account-U0dbRcKS","name":"NetAppHCL"}]', 'token': '****************']
Blanchet account_id: [account-yX7cS8vU]
Demo_SIM account_id: [account-j3aZttuL]
NetAppHCL account_id: [account-U0dbRcKS]
```