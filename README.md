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

## How to use this script
# Create the Script configuratoin File with your NetApp Cloud Credential

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
        <img src="Pictures/Refresh-Token-Generator.png" alt="NetApp Refresh Token" width="1100" height="350">
        - Create the Configuration File : Example for Linux:
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

    - for more information please go to https://services.cloud.netapp.com/developer-hub 
- Non-Federated users (Regular Access)


