#################################################################################################
# API Cloud NetApp Version 0.5
# jerome.blanchet@netapp.com
#################################################################################################
import ssl
import json
import OpenSSL 
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import configparser
import os

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

#################################################################################################
# Global Parameters for ontap rest module 
# https://docs.netapp.com/us-en/occm/api_sync.html
#################################################################################################
API_OCCM = "https://cloudmanager.cloud.netapp.com"
API_CLOUDSYNC = "https://api.cloudsync.netapp.com"
API_CLOUDAUTH = "https://netapp-cloud-account.auth0.com"
API_AUDIENCE = "https://api.cloud.netapp.com"
API_SERVICES = "https://api.services.cloud.netapp.com"
CLIENT_ID_REGULAR = "QC3AgHk6qdbmC7Yyr82ApBwaaJLwRrNO" 
CLIENT_ID_REFRESH_TOKEN = "Mu0V1ywgYteI6w1MbD15fKfVIUrNXGWC"
API_RELEASE='0.6.1'
#################################################################################################
# Debug 
#################################################################################################
Debug=False

#################################################################################################
# print debug
#################################################################################################
def print_deb (debug_var):
    if (Debug):
        print("DEBUG_API: [", end="") 
        print(debug_var,end="]\n")

#################################################################################################
def create_API_config_file (API_config_file, API_account_info):

    print_deb("FUNCTION: create_API_config_file")
    file_info={} 
    file_info["status"]="unknown"

    config = configparser.ConfigParser()
    config['DEFAULT'] = {'version' : '1', 'update' : '1'}
    config['API_LOGIN'] = {}
    config['API_TOKEN'] = {}
    config['API_LOGIN']['grant_type'] = API_account_info["grant_type"] 
    if ( API_account_info["grant_type"] == "refresh_token" ):
         config['API_LOGIN']['refresh_token'] = API_account_info["refresh_token"]
         config['API_LOGIN']['client_id'] = CLIENT_ID_REFRESH_TOKEN
    else:
         config['API_LOGIN']['username'] = API_account_info["username"]
         config['API_LOGIN']['password'] = API_account_info["password"]
         config['API_LOGIN']['audience'] = API_AUDIENCE
         config['API_LOGIN']['client_id'] = CLIENT_ID_REGULAR
    try:
         with open(API_config_file, 'w') as configfile:
              config.write(configfile)
    except configparser.Error as e:
         file_info["status"]="failed"
         file_info["message"]=e
         return file_info
    file_info["status"]="success"
    file_info["message"]="ok"
    return file_info
#################################################################################################
def check_API_config_file (API_config_file):

    print_deb("FUNCTION: check_API_config_file")
    file_info={} 
    file_info["status"]="unknown"
    
    if (os.path.isfile(API_config_file) != True ):
         file_info["status"]="failed"
         file_info["message"]="ERROR: {0} file not found".format(API_config_file)
         return file_info 

    config = configparser.ConfigParser()

    try:
         config.read(API_config_file)
    except configparser.Error as e:
         file_info["message"]=e
         return file_info

    try:
         section=config['DEFAULT'] ; print_deb("DEFAULT: {0} ".format(section))
    except KeyError as e:
         file_info["message"]=e
         return file_info
    try:
         section=config['API_LOGIN'] ; print_deb("API_LOGIN: {0} ".format(section))
    except KeyError as e:
         print_deb("section [API_LOGIN] not found in config file: add section")
         file_info["status"]="update"
         config['API_LOGIN']={}

    try:
         section=config['API_TOKEN'] ; print_deb("API_TOKEN: {0} ".format(section))
    except KeyError as e:
         print_deb("section [API_TOKEN] not found in config file: add section")
         file_info["status"]="update"
         config['API_TOKEN']={}

    if (file_info["status"] == "update"):
         try:
              with open(API_config_file, 'w') as configfile:
                   config.write(configfile)
         except configparser.Error as e:
              file_info["status"]="failed"
              file_info["message"]=e
              return file_info

    file_info["status"]="success"
    return file_info

#################################################################################################
# Token management API
#################################################################################################
def create_new_token (API_config_file):

    print_deb("FUNCTION: create_new_token")
    token_info={} 
    token_info["status"]="unknown"

    if (os.path.isfile(API_config_file) != True ):
         token_info["status"]="failed"
         token_info["message"]="ERROR: {0} file not found".format(API_config_file)
         return token_info 

 
    config = configparser.ConfigParser()

    try:
         config.read(API_config_file)
    except configparser.Error as e:
         token_info["message"]=e
         return token_info

    try:
         update=int(config['DEFAULT']['update']); update+=1
    except KeyError as e:
         update = 0

    try:
        grant_type=config['API_LOGIN']['grant_type']; print_deb("grant_type: {0} ".format(grant_type))
    except KeyError as e:
         token_info["status"]="failed"
         token_info["message"]="ERROR: {0} in configuration file {1}".format(e,API_config_file)
         return token_info 

    if ( grant_type == "password"):
         try:
              username=config['API_LOGIN']['username']; print_deb("username: {0} ".format(username))
              password=config['API_LOGIN']['password']; print_deb("password: {0} ".format(password))
              audience=config['API_LOGIN']['audience']; print_deb("audience: {0} ".format(audience))
              client_id=config['API_LOGIN']['client_id']; print_deb("client_id: {0} ".format(client_id))
         except KeyError as e:
              token_info["status"]="failed"
              token_info["message"]="ERROR: {0} in configuration file {1}".format(e,API_config_file)
              return token_info 
         
         # Create data  Request to get the token with password 
         data = {
              "grant_type": grant_type,
              "username": username,
              "password": password,
              "audience": audience,
              "client_id": client_id
         }

    else:
         if ( grant_type == "refresh_token" ):
              try:
                   refresh_token=config['API_LOGIN']['refresh_token']; print_deb("refresh_token : {0} ".format(refresh_token))
                   client_id=config['API_LOGIN']['client_id']; print_deb("client_id : {0} ".format(client_id))
              except KeyError as e:
                   token_info["status"]="failed"
                   token_info["message"]="ERROR: {0} in configuration file {1}".format(e,API_config_file)
                   return token_info 

              # Create data Request to get the token with refresh_token 
              data = {
                   "grant_type": grant_type,
                   "refresh_token": refresh_token,
                   "client_id": client_id 
              }

              # End Token get for token_refresh method  
         else:
              token_info["status"]="failed"
              token_info["message"]="ERROR: grant_type unknown in configuration file {0}".format(API_config_file)
              return token_info

    # sent the oauth token request
    print_deb(data)
    try:
         url = API_CLOUDAUTH + "/oauth/token"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {'Content-type': 'application/json'} 
         response = requests.post(url, json=data, headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         token_info["status"]="failed"
         token_info["message"]=e
         return token_info 
    if ( response == {} ):
         token_info["status"]="failed"
         token_info["message"]="Error null response request"
         return token_info

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code=='200'):
         token_info["status"]="success"
         # Get the new token 
         content = json.loads(response.content)
         try:
              token=format(content['access_token'])
         except KeyError as e:
              token_info["status"]="failed"
              token_info["message"]="ERROR: {0} not found in request {1}".format(e,url)
              return token_info 
         print_deb("new token:[{0}]".format(token))
         token_info["message"]=response.text
         token_info["token"]=token

         # Update new token in configuration file
         config['DEFAULT']['update'] = "{0}".format(update)
         config['API_TOKEN']['access_token'] = token
         try:
              with open(API_config_file, 'w') as configfile:
                  config.write(configfile)
         except configparser.Error as e:
              token_info["status"]="failed"
              token_info["message"]=e
         return token_info

    else:
          token_info["status"]="failed"
          token_info["message"]=response.text
          return token_info
 
#################################################################################################
def check_current_token (API_config_file):
   
    print_deb("FUNCTION: check_current_token")
    token_info={}
    token_info["status"]="unknown"

    if (os.path.isfile(API_config_file) != True ):
         token_info["status"]="failed"
         token_info["message"]="ERROR: {0} file not found".format(API_config_file)
         return token_info 
 
    config = configparser.ConfigParser()
    try:
         config.read(API_config_file)
    except configparser.Error as e:
         token_info["message"]=e
         return token_info 

    # Get token form the configuration file 
    try:
         token=config['API_TOKEN']['access_token']; print_deb("access_token: {0} ".format(token))
    except KeyError as e:
         token_info["status"]="failed"
         token_info["message"]="ERROR: {0} in configuration file {1}".format(e,API_config_file)
         return token_info 

    if ( token == '' ):
         token_info["status"]="failed"
         token_info["message"]="ERROR: access_token empty in configuration file {0}".format(API_config_file)
         return token_info

    try:
         url = API_OCCM + "/tenancy/account"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {'Content-type': 'application/json'} 
         response = requests.get(url, auth=BearerAuth(token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         token_info["status"]="failed"
         token_info["message"]=e
         return token_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         token_info["status"]="success"
         token_info["message"]="ok"
         token_info["accounts"]=response.text
         token_info["token"]=token
         return token_info
    else:
         token_info["status"]="failed"
         token_info["message"]=response.text
         return token_info

#################################################################################################
def get_current_account(API_config_file):

    print_deb("FUNCTION: get_current_account")
    account_info={}
    account_info["status"]="unknow"

    if (os.path.isfile(API_config_file) != True ):
         account_info["status"]="failed"
         account_info["message"]="ERROR: {0} file not found".format(API_config_file)
         return account_info 

    config = configparser.ConfigParser()

    try:
         config.read(API_config_file)
    except configparser.Error as e:
         account_info["message"]=e
         return account_info

    try:
        current_account_id=config['API_LOGIN']['current_account_id']; print_deb("grant_type: {0} ".format(current_account_id))
    except KeyError as e:
         account_info["status"]="failed"
         account_info["message"]="ERROR: {0} in configuration file {1}".format(e,API_config_file)
         return account_info 
     
    account_info["status"]="success"
    account_info["current_account_id"]=current_account_id

    return account_info 

#################################################################################################
def set_current_account (API_token, API_config_file, API_accountID):

    print_deb("FUNCTION: set_current_account")
    accounts_found=False
    accounts_info={}

    accounts_info=occm_get_accounts_list(API_token)
    if (accounts_info["status"] == "success"):
         accounts=json.loads(accounts_info["accounts"])
         for account in accounts:
             if ( account["accountPublicId"] == API_accountID ):
                  accounts_found=True
    if ( accounts_found == True ):
         accounts_info["default"]=API_accountID
         # Save Default Account in configuration file 
         if (os.path.isfile(API_config_file) != True ):
              accounts_info["status"]="failed"
              accounts_info["message"]="{0} Configuration file not found".format(API_config_file)
              return accounts_info
          
         config = configparser.ConfigParser()

         try:
              config.read(API_config_file)
         except configparser.Error as e:
              accounts_info["message"]=e
              return accounts_info
         try:
              update=int(config['DEFAULT']['update']); update+=1
         except KeyError as e:
              update = 0       

         config['DEFAULT']['update'] = "{0}".format(update)
         config['API_LOGIN']['current_account_id'] = API_accountID

         try:
              with open(API_config_file, 'w') as configfile:
                  config.write(configfile)
         except configparser.Error as e:
              accounts_info["status"]="failed"
              accounts_info["message"]=e
         return accounts_info           

    else:
         accounts_info["status"]="failed"
         accounts_info["message"]="account_id {0} not found".format(API_accountID)
         accounts_info["default"]=""

    return accounts_info

#################################################################################################
def occm_get_accountName (API_token, API_accountID):
    print_deb("FUNCTION: set_current_account")
    accountName=""
    accounts_info={}

    accounts_info=occm_get_accounts_list(API_token)
    if (accounts_info["status"] == "success"):
         accounts=json.loads(accounts_info["accounts"])
         for account in accounts:
             if ( account["accountPublicId"] == API_accountID ):
                  accountName=account["accountName"] 

    return accountName 

#################################################################################################
def occm_get_accounts_list (API_token):
   
    print_deb("FUNCTION: occm_get_account_list")
    accounts_info={}
    accounts_info["status"]="unknown"

    if ( API_token == '' ):
         accounts_info["status"]="failed"
         accounts_info["message"]="ERROR: miss token"
         return accounts_info

    try:
         url = API_OCCM + "/tenancy/account"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {'Content-type': 'application/json'} 
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         accounts_info["status"]="failed"
         accounts_info["message"]=e
         return accounts_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         accounts_info["status"]="success"
         accounts_info["message"]="ok"
         accounts_info["accounts"]=response.text
         accounts_info["token"]=API_token
         return accounts_info
    else:
         accounts_info["status"]="failed"
         accounts_info["message"]=response.text
         return accounts_info

#################################################################################################
def occm_get_workspaces_list (API_token, API_accountID):
   
    print_deb("FUNCTION: occm_get_workspaces_list")
    workspaces_info={}
    workspaces_info["status"]="unknown"

    if ( API_token == '' ):
         workspaces_info["status"]="failed"
         workspaces_info["message"]="ERROR: miss token"
         return workspaces_info

    try:
         url = API_OCCM + "/tenancy/account/" + API_accountID + "/workspace"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {'Content-type': 'application/json'} 
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         workspaces_info["status"]="failed"
         workspaces_info["message"]=e
         return workspaces_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         workspaces_info["status"]="success"
         workspaces_info["message"]="ok"
         workspaces_info["accounts"]=response.text
         return workspaces_info
    else:
         workspaces_info["status"]="failed"
         workspaces_info["message"]=response.text
         return workspaces_info

#################################################################################################
def occm_get_occms_list (API_token, API_accountID):
   
    print_deb("FUNCTION: occm_get_occms_list")
    occms_info={}
    occms_info["status"]="unknown"

    if ( API_token == '' ):
         occms_info["status"]="failed"
         occms_info["message"]="ERROR: miss token"
         return occms_info

    try:
         url = API_SERVICES + "/occm/list-occms/" + API_accountID
         print_deb("url: {0} ".format(url))
         response={}
         headers = {'Content-type': 'application/json'}
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         occms_info["status"]="failed"
         occms_info["message"]=e
         return occms_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         occms_info["status"]="success"
         occms_info["message"]="ok"
         occms_info["occms"]=response.text
         return occms_info
    else:
         occms_info["status"]="failed"
         occms_info["message"]=response.text
         return occms_info


#################################################################################################
def get_current_occm_agent(API_config_file):

    print_deb("FUNCTION: get_current_occm_agentt")
    occm_info={}
    occm_info["status"]="unknow"

    if (os.path.isfile(API_config_file) != True ):
         occm_info["status"]="failed"
         occm_info["message"]="ERROR: {0} file not found".format(API_config_file)
         return occm_info 

    config = configparser.ConfigParser()

    try:
         config.read(API_config_file)
    except configparser.Error as e:
         occm_info["message"]=e
         return occm_info

    try:
        current_agent_id=config['API_LOGIN']['current_agent_id']; print_deb("grant_type: {0} ".format(current_agent_id))
    except KeyError as e:
         occm_info["status"]="failed"
         occm_info["message"]="ERROR: {0} in configuration file {1}".format(e,API_config_file)
         return occm_info 
     
    occm_info["status"]="success"
    occm_info["current_agent_id"]=current_agent_id

    return occm_info 

#################################################################################################
def set_current_occm_agent (API_token, API_config_file, API_accountID, API_agentID):

    print_deb("FUNCTION: set_current_account")
    occm_found=False
    occms_info={}

    occms_info=occm_get_occms_list(API_token,API_accountID)
    if (occms_info["status"] == "success"):
         occms=json.loads(occms_info["occms"])
         agents=occms["occms"]
         for agent in agents:
             if ( agent["agent"]["agentId"] == API_agentID ):
                  occm_found=True
    if ( occm_found == True ):
         occms_info["default"]=API_agentID
         # Save Default Account in configuration file 
         if (os.path.isfile(API_config_file) != True ):
              occms_info["status"]="failed"
              occms_info["message"]="{0} Configuration file not found".format(API_config_file)
              return occms_info
          
         config = configparser.ConfigParser()

         try:
              config.read(API_config_file)
         except configparser.Error as e:
              occms_info["message"]=e
              return occms_info
         try:
              update=int(config['DEFAULT']['update']); update+=1
         except KeyError as e:
              update = 0       

         config['DEFAULT']['update'] = "{0}".format(update)
         config['API_LOGIN']['current_agent_id'] = API_agentID

         try:
              with open(API_config_file, 'w') as configfile:
                  config.write(configfile)
         except configparser.Error as e:
              occms_info["status"]="failed"
              occms_info["message"]=e
         return occms_info           

    else:
         occms_info["status"]="failed"
         occms_info["message"]="account_id {0} not found".format(API_accountID)
         occms_info["default"]=""

    return occms_info

#################################################################################################
def occm_get_cloud_accounts_list (API_token, API_accountID, API_agentID):
   
    print_deb("FUNCTION: occm_get_cloud_accounts_list")
    cloudaccounts_info={}
    cloudaccounts_info["status"]="unknown"

    try:
         url = API_OCCM + "/occm/api/accounts"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cloudaccounts_info["status"]="failed"
         cloudaccounts_info["message"]=e
         return cloudaccounts_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         cloudaccounts_info["status"]="success"
         cloudaccounts_info["message"]="ok"
         cloudaccounts_info["accounts"]=response.text
         return cloudaccounts_info
    else:
         cloudaccounts_info["status"]="failed"
         cloudaccounts_info["message"]=response.text
         return cloudaccounts_info

#################################################################################################
# CVO Working Environments  
#################################################################################################
def cvo_get_working_environment (API_token, API_accountID, API_agentID, vsa_id):
    print_deb("FUNCTION: cvo_get_working_environments")
    cvo_info={}
    cvo_info["status"]="unknown"

    url = API_OCCM + "/occm/api/working-environments/" + vsa_id

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvo_info["status"]="failed"
         cvo_info["message"]=e
         return cvo_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvo_info["status"]="success"
         cvo_info["message"]="ok"
         cvo_info["cvo"]=response.text
         return cvo_info
    else:
              cvo_info["status"]="failed"
              cvo_info["message"]=response.text
              return cvo_info

#################################################################################################
# CVO Azure API
#################################################################################################
def cvo_azure_get_vsa_list (API_token, API_accountID, API_agentID ):

    print_deb("FUNCTION: cvo_azure_get_vsa_list")
    cvos_info={}
    cvos_info["status"]="unknown"

    url = API_OCCM + "/occm/api/azure/vsa/working-environments?fields=status"
    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvos_info["status"]="failed"
         cvos_info["message"]=e
         return cvos_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvos_info["status"]="success"
         cvos_info["message"]="ok"
         cvos_info["cvos"]=response.text
         return cvos_info
    else:
              cvos_info["status"]="failed"
              cvos_info["message"]=response.text
              return cvos_info

#################################################################################################
def cvo_azure_get_vsa (API_token, API_accountID, API_agentID, isHA, vsa_id):

    print_deb("FUNCTION: cvo_azure_get_vsa")
    cvo_info={}
    cvo_info["status"]="unknown"

    if( isHA == True ):
         url = API_OCCM + "/occm/api/azure/ha/working-environments/" + vsa_id + "?fields=*"
    else:
         url = API_OCCM + "/occm/api/azure/vsa/working-environments/" + vsa_id + "?fields=*"

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvo_info["status"]="failed"
         cvo_info["message"]=e
         return cvo_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvo_info["status"]="success"
         cvo_info["message"]="ok"
         cvo_info["cvo"]=response.text
         return cvo_info
    else:
              cvo_info["status"]="failed"
              cvo_info["message"]=response.text
              return cvo_info

#################################################################################################
def cvo_azure_create_new (API_token, API_accountID, API_agentID, isHA, API_json ):

    print_deb("FUNCTION: cvo_azure_create_new_single")
    cvo_info={}
    cvo_info["status"]="unknown"

    if ( isHA == True ):
         url = API_OCCM + "/occm/api/azure/ha/working-environments"
    else:
         url = API_OCCM + "/occm/api/azure/vsa/working-environments"

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.post(url, auth=BearerAuth(API_token), headers=headers,json=API_json)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvo_info["status"]="failed"
         cvo_info["message"]=e
         return cvo_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvo_info["status"]="success"
         cvo_info["message"]="ok"
         cvo_info["cvo"]=response.text
         return cvo_info
    else:
         cvo_info["status"]="failed"
         cvo_info["message"]=response.text
         return cvo_info

#################################################################################################
def cvo_azure_delete_vsa (API_token, API_accountID, API_agentID, isHA, vsa_id):

    print_deb("FUNCTION: cvo_azure_delete_vsa")
    cvos_info={}
    cvos_info["status"]="unknown"

    if ( isHA == True ):
         url = API_OCCM + "/occm/api/azure/ha/working-environments/" + vsa_id
    else:
         url = API_OCCM + "/occm/api/azure/vsa/working-environments/" + vsa_id

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.delete(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvos_info["status"]="failed"
         cvos_info["message"]=e
         return cvos_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvos_info["status"]="success"
         cvos_info["message"]="ok"
         cvos_info["cvo"]=response.text
         return cvos_info
    else:
              cvos_info["status"]="failed"
              cvos_info["message"]=response.text
              return cvos_info

#################################################################################################
def cvo_azure_action_vsa (API_token, API_accountID, API_agentID, vsa_id, isHA, action):

    print_deb("FUNCTION: cvo_azure_stop_vsa")
    cvos_info={}
    cvos_info["status"]="unknown"

    if ( isHA == True ):
        API_PATH = "/occm/api/azure/ha/working-environments/"
    else: 
        API_PATH = "/occm/api/azure/vsa/working-environments/"

    if ( action == "start" ):
        url = API_OCCM + API_PATH + vsa_id + "/start"
        action_check=True

    if ( action == "stop" ):
        url = API_OCCM + API_PATH + vsa_id + "/stop"
        action_check=True

    if (action_check != True ):
         cvos_info["status"]="failed"
         cvos_info["message"]="ERROR: bad action [{0}]".format(action)
         return cvos_info

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.post(url, auth=BearerAuth(API_token), headers=headers)

    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvos_info["status"]="failed"
         cvos_info["message"]=e
         return cvos_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvos_info["status"]="success"
         cvos_info["message"]="ok"
         cvos_info["cvo"]=response.text
         return cvos_info
    else:
         cvos_info["status"]="failed"
         cvos_info["message"]=response.text
         return cvos_info

#################################################################################################
# CVO AWS API
#################################################################################################
def cvo_aws_get_vsa_list (API_token, API_accountID, API_agentID ):

    print_deb("FUNCTION: cvo_aws_get_vsa_list")
    cvos_info={}
    cvos_info["status"]="unknown"

    url = API_OCCM + "/occm/api/vsa/working-environments?fields=status"
    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvos_info["status"]="failed"
         cvos_info["message"]=e
         return cvos_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvos_info["status"]="success"
         cvos_info["message"]="ok"
         cvos_info["cvos"]=response.text
         return cvos_info
    else:
              cvos_info["status"]="failed"
              cvos_info["message"]=response.text
              return cvos_info

#################################################################################################
def cvo_aws_get_vsa (API_token, API_accountID, API_agentID, isHA, vsa_id):

    print_deb("FUNCTION: cvo_aws_get_vsa")
    cvo_info={}
    cvo_info["status"]="unknown"

    if( isHA == True ):
         url = API_OCCM + "/occm/api/aws/ha/working-environments/" + vsa_id + "?fields=*"
    else:
         url = API_OCCM + "/occm/api/vsa/working-environments/" + vsa_id + "?fields=*"

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvo_info["status"]="failed"
         cvo_info["message"]=e
         return cvo_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvo_info["status"]="success"
         cvo_info["message"]="ok"
         cvo_info["cvo"]=response.text
         return cvo_info
    else:
              cvo_info["status"]="failed"
              cvo_info["message"]=response.text
              return cvo_info

#################################################################################################
def cvo_aws_create_new (API_token, API_accountID, API_agentID, isHA, API_json ):

    print_deb("FUNCTION: cvo_aws_create_new_single")
    cvo_info={}
    cvo_info["status"]="unknown"

    if ( isHA == True ):
         url = API_OCCM + "/occm/api/aws/ha/working-environments"
    else:
         url = API_OCCM + "/occm/api/vsa/working-environments"

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.post(url, auth=BearerAuth(API_token), headers=headers,json=API_json)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvo_info["status"]="failed"
         cvo_info["message"]=e
         return cvo_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvo_info["status"]="success"
         cvo_info["message"]="ok"
         cvo_info["cvo"]=response.text
         return cvo_info
    else:
         cvo_info["status"]="failed"
         cvo_info["message"]=response.text
         return cvo_info

#################################################################################################
def cvo_aws_delete_vsa (API_token, API_accountID, API_agentID, isHA, vsa_id):

    print_deb("FUNCTION: cvo_aws_delete_vsa")
    cvos_info={}
    cvos_info["status"]="unknown"

    if ( isHA == True ):
         url = API_OCCM + "/occm/api/aws/ha/working-environments/" + vsa_id
    else:
         url = API_OCCM + "/occm/api/vsa/working-environments/" + vsa_id

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.delete(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvos_info["status"]="failed"
         cvos_info["message"]=e
         return cvos_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvos_info["status"]="success"
         cvos_info["message"]="ok"
         cvos_info["cvo"]=response.text
         return cvos_info
    else:
              cvos_info["status"]="failed"
              cvos_info["message"]=response.text
              return cvos_info

#################################################################################################
def cvo_aws_action_vsa (API_token, API_accountID, API_agentID, vsa_id, isHA, action):

    print_deb("FUNCTION: cvo_aws_stop_vsa")
    cvos_info={}
    cvos_info["status"]="unknown"

    if ( isHA == True ):
        API_PATH = "/occm/api/aws/ha/working-environments/"
    else: 
        API_PATH = "/occm/api/vsa/working-environments/"

    if ( action == "start" ):
        url = API_OCCM + API_PATH + vsa_id + "/start"
        action_check=True

    if ( action == "stop" ):
        url = API_OCCM + API_PATH + vsa_id + "/stop"
        action_check=True

    if (action_check != True ):
         cvos_info["status"]="failed"
         cvos_info["message"]="ERROR: bad action [{0}]".format(action)
         return cvos_info

    try:
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "X-Tenancy-Account-Id": API_accountID , "X-Agent-Id": API_agentID }
         print_deb("headers: {0} ".format(headers))
         response = requests.post(url, auth=BearerAuth(API_token), headers=headers)

    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         cvos_info["status"]="failed"
         cvos_info["message"]=e
         return cvos_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         cvos_info["status"]="success"
         cvos_info["message"]="ok"
         cvos_info["cvo"]=response.text
         return cvos_info
    else:
         cvos_info["status"]="failed"
         cvos_info["message"]=response.text
         return cvos_info

#################################################################################################
# Cloudsync API
#################################################################################################
def cloudsync_get_accounts_list (API_token):
   
    print_deb("FUNCTION: cloudsync_get_accounts_list")
    accounts_info={}
    accounts_info["status"]="unknown"

    try:
         url = API_CLOUDSYNC + "/api/accounts"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {'Content-type': 'application/json'} 
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         accounts_info["status"]="failed"
         accounts_info["message"]=e
         return accounts_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         accounts_info["status"]="success"
         accounts_info["message"]="ok"
         accounts_info["accounts"]=response.text
         accounts_info["token"]=API_token
         return accounts_info
    else:
         accounts_info["status"]="failed"
         accounts_info["message"]=response.text
         return accounts_info

#################################################################################################
def cloudsync_get_databrokers_list (API_token, API_accountID):
   
    print_deb("FUNCTION: cloudsync_get_databrokers_list")
    databrokers_info={}
    databrokers_info["status"]="unknown"

    try:
         url = API_CLOUDSYNC + "/api/data-brokers"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "x-account-id": API_accountID }
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         databrokers_info["status"]="failed"
         databrokers_info["message"]=e
         return databrokers_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( status_code == '200' ):
         databrokers_info["status"]="success"
         databrokers_info["message"]="ok"
         databrokers_info["databrokers"]=response.text
         return databrokers_info
    else:
         databrokers_info["status"]="failed"
         databrokers_info["message"]=response.text
         return databrokers_info

#################################################################################################
def cloudsync_create_relations (API_token, API_accountID, API_json):

    print_deb("FUNCTION: cloudsync_create_relations")
    relations_info={}

    try:
         url = API_CLOUDSYNC + "/api/relationships-v2"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "x-account-id": API_accountID }
         response = requests.post(url, auth=BearerAuth(API_token), headers=headers, json=API_json)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         relations_info["status"]="failed"
         relations_info["message"]=e
         return relations_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         relations_info["status"]="success"
         relations_info["message"]="ok"
         relations_info["relations"]=response.text
         return relations_info
    else:
              relations_info["status"]="failed"
              relations_info["message"]=response.text
              return relations_info

#################################################################################################
def cloudsync_get_relations (API_token, API_accountID):

    print_deb("FUNCTION: cloudsync_get_relations")
    relations_info={}

    try:
         url = API_CLOUDSYNC + "/api/relationships-v2"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "x-account-id": API_accountID }
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         relations_info["status"]="failed"
         relations_info["message"]=e
         return relations_info 

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         relations_info["status"]="success"
         relations_info["message"]="ok"
         relations_info["relations"]=response.text
         return relations_info
    else:
         relations_info["status"]="failed"
         relations_info["message"]=response.text
         return relations_info

#################################################################################################
def cloudsync_get_relation (API_token, API_accountID, relation_id):

    print_deb("FUNCTION: cloudsync_get_relation")
    relation_info={}

    try:
         url = API_CLOUDSYNC + "/api/relationships-v2/" + relation_id
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "x-account-id": API_accountID }
         response = requests.get(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         relation_info["status"]="failed"
         relation_info["message"]=e
         return relation_info

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         relation_info["status"]="success"
         relation_info["message"]="ok"
         relation_info["relation"]=response.text
         return relation_info
    else:
         relation_info["status"]="failed"
         relation_info["message"]=response.text
         return relation_info

#################################################################################################
def cloudsync_sync_relation (API_token, API_accountID, relation_id):

    print_deb("FUNCTION: cloudsync_sync_relation")
    relation_info={}
    relation_info["status"]="unknown"

    try:
         url = API_CLOUDSYNC + "/api/relationships/" + relation_id + "/sync"
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "x-account-id": API_accountID }
         response = requests.put(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         relation_info["status"]="failed"
         relation_info["message"]=e
         return relation_info

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb("ok {0}".format(response.ok))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         relation_info["status"]="success"
         relation_info["message"]="ok"
         relation_info["relations"]=response.text
         return relation_info
    else:
              relation_info["status"]="failed"
              relation_info["message"]=response.text
              return relation_info

#################################################################################################
def cloudsync_delete_relation (API_token, API_accountID, relation_id):

    print_deb("FUNCTION: cloudsync_delete_relation")
    relation_info={}
    relation_info["status"]="unknown"

    try:
         url = API_CLOUDSYNC + "/api/relationships/" + relation_id
         print_deb("url: {0} ".format(url))
         response={}
         headers = {"Content-type": "application/json", "x-account-id": API_accountID }
         response = requests.delete(url, auth=BearerAuth(API_token), headers=headers)
    except BaseException as e:
         print_deb("ERROR: Request {0} Failed: {1}".format(url,e))
         relation_info["status"]="failed"
         relation_info["message"]=e
         return relation_info

    status_code=format(response.status_code)
    print_deb("status_code: {0}".format(status_code))
    print_deb ("text: {0}".format(response.text))
    print_deb ("content: {0}".format(response.content))
    print_deb ("reason: {0}".format(response.reason))

    if ( response.ok ):
         relation_info["status"]="success"
         relation_info["message"]="ok"
         relation_info["relations"]=response.text
         return relation_info
    else:
              relation_info["status"]="failed"
              relation_info["message"]=response.text
              return relation_info
