#####################################################################
# cloudaccount is a simple python script using NetApp Cloud Rest API
# jerome.blanchet@netapp.com
#####################################################################
import netapp_api_cloud
import argparse
import getpass
import sys
import configparser
import json
import os

RELEASE='0.3'
#####################################################################
# Local API 
#####################################################################
Debug = False

def print_vers():
      print (RELEASE)

def print_syntax_error(mess):
      print ('ERROR: {0}'.format(mess))

def print_deb (debug_var):
    if (Debug):
        print("DEBUG: [", end="") 
        print(debug_var,end="]\n")

#####################################################################
# API Configuration file 
#####################################################################
from sys import platform
if (platform == "win32") :
    print_deb("Another Win32 system")
    username=os.environ.get('username')
    homedrive=os.environ.get('homedrive')
    homepath=os.environ.get('homepath')
    API_DIR=homedrive + homepath + "\\NetAppCloud"
    API_CONFIG_FILE= API_DIR + '\\api.conf'
else:
    USER=os.environ.get('USER')
    HOME=os.environ.get('HOME')
    API_DIR= HOME  + "/NetAppCloud"
    API_CONFIG_FILE= API_DIR + '/api.conf'

if ( os.path.isdir(API_DIR) != True ):
    os.mkdir(API_DIR)

#####################################################################
# Main
#####################################################################
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", dest='debug', help="debug mode", action="store_true")
parser.add_argument("-j", "--json", dest='json', help="print in json format", action="store_true")
parser.add_argument("--account-id", dest='account_id', help="select NetApp Cloud account ID")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--setup", dest='setup', help="setup NetApp cloud API connection", action="store_true" )
group.add_argument("--account-list", dest='account_list', help="print NetApp cloud accounts list", action="store_true" )
group.add_argument("--workspace-list", dest='workspace_list', help="print NetApp cloud accounts list", action="store_true" )
group.add_argument("--set-default-account", dest='default_account_id', help="set default NetApp Cloud account")
group.add_argument("--check-token", dest='check_token', help="check NetApp Cloud access token", action="store_true" )
group.add_argument("--get-new-token", dest='get_new_token', help="get new NetApp Cloud access token", action="store_true" )
args = parser.parse_args()

if args.debug:
      Debug = True
      netapp_api_cloud.Debug = True 

try:

    # Get Account Information from the config file
    account_info=netapp_api_cloud.get_default_account(API_CONFIG_FILE)
    if (account_info["status"] == "success"):
         account_id = account_info["default_account_id"] 
    else:
         account_id = ""

    # args options 
    if args.account_id:
         account_id = args.account_id 

    if args.setup:

         # Create API configuration file
         account_info = {}
         if (os.path.isfile(API_CONFIG_FILE) == True ):
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: File {0} already exist. Erase the file ? [y/n] : '.format(API_CONFIG_FILE))
              if ( answer != "y"):
                   exit(0)
         federated_user = '' ;  refresh_token = ''; password='' ; username = '' 
         while ( federated_user != "y" and federated_user != "n" ) :
              federated_user=input('Is your NetApp Cloud Central use federated users ? [y/n] : ')
         if (federated_user == "y"):
              print("To get your Refresh Token please go to : https://services.cloud.netapp.com/refresh-token ")
              if (len(refresh_token)==0): refresh_token=input('NetApp Cloud Central Refresh Token : ')
              account_info["grant_type"] = "refresh_token" 
              account_info["refresh_token"] = refresh_token
         else: 
              if (len(username)==0): username=input('NetApp Cloud Central Email : ')
              if (len(password)==0): password=getpass.getpass('NetApp Cloud Central Password : ')
              account_info["grant_type"] = "password" 
              account_info["username"] = username 
              account_info["password"] = password 

         print_deb(account_info)
         file_info = netapp_api_cloud.create_API_config_file(API_CONFIG_FILE, account_info)
         if ( file_info["status"] != "success" ):
              print("ERROR: {0}".format(file_info["message"]))
              exit(1)

         # Create New Token during setup
         token_info=netapp_api_cloud.create_new_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
         API_TOKEN=token_info["token"]

         # Set Default Account during setup
         accounts_info=netapp_api_cloud.occm_get_accounts_list(API_TOKEN)
         if (accounts_info["status"] != "success"):
              print("ERROR: {0}".format(accounts_info["message"]))
         accounts=json.loads(accounts_info["accounts"])
         if (len(accounts) == 1):
              account=accounts[0]
              accounts_info=netapp_api_cloud.occm_set_default_account(API_TOKEN, API_CONFIG_FILE,account["accountPublicId"])
              if (accounts_info["status"] != "success"):
                   print("ERROR: {0}".format(accounts_info["message"]))
         else:
              for account in accounts:
                   print("Name:[{0}] account_id:[{1}]".format(account["accountName"], account["accountPublicId"]))
              accounts_info["status"] = ""
              while ( accounts_info["status"] != "success" ) :
                   default_account_id=input('Please enter your selected default account_id : ')
                   accounts_info=netapp_api_cloud.occm_set_default_account(API_TOKEN, API_CONFIG_FILE,default_account_id)
                   if (accounts_info["status"] != "success"):
                        print("ERROR: {0}".format(accounts_info["message"]))
    else: 
         file_info = netapp_api_cloud.check_API_config_file(API_CONFIG_FILE)
         if ( file_info["status"] != "success" ):
              print("ERROR: {0}".format(file_info["message"]))
              exit(1)

    if args.get_new_token:

         token_info=netapp_api_cloud.create_new_token(API_CONFIG_FILE)
         if ( token_info["status"] == "success" ):
              API_TOKEN=token_info["token"]
              print_deb("API_TOKEN: {0}".format(API_TOKEN))
         else:
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
    else: 

         print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] == "success" ):
              API_TOKEN=token_info["token"]
              print_deb("API_TOKEN: {0}".format(API_TOKEN))
         else:
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)

    if args.account_list:

         account_info=netapp_api_cloud.get_default_account(API_CONFIG_FILE)
         if (account_info["status"] == "success"):
              default_account_id = account_info["default_account_id"] 
         else:
              default_account_id = ""
         accounts_info=netapp_api_cloud.occm_get_accounts_list(API_TOKEN)
         print_deb(accounts_info)
         if (accounts_info["status"] == "success"):
              accounts=json.loads(accounts_info["accounts"])
              print("Print NetApp Account list[{0}]:".format(len(accounts)))
              if (args.json):
                   print(json.dumps(accounts, indent=4))
              else:
                   for account in accounts:
                        if ( account["accountPublicId"] == default_account_id ):
                             print("Name:[{0}] account_id:[{1}] Default:[X]".format(account["accountName"], account["accountPublicId"]))
                        else:
                             print("Name:[{0}] account_id:[{1}] Default:[ ]".format(account["accountName"], account["accountPublicId"]))
         else:
              print("ERROR: {0}".format(accounts_info["message"]))
              exit(1)

#ASP
    if args.workspace_list:

         workspaces_info=netapp_api_cloud.occm_get_workspaces_list(API_TOKEN,account_id)
         print_deb(workspaces_info)
         if (workspaces_info["status"] == "success"):
              workspaces=json.loads(workspaces_info["accounts"])
              print("Print NetApp Workspaceslist[{0}]:".format(len(workspaces)))
              if (args.json):
                   print(json.dumps(workspaces, indent=4))
              else:
                   for workspace in workspaces:
                        print("Name:[{0}] id:[{1}]".format(workspace["workspaceName"], workspace["workspacePublicId"]))
         else:
              print("ERROR: {0}".format(workspaces_info["message"]))
              exit(1)
#ASP

    if args.check_token:
         # Get Token and cloud manager account informations 
         print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] == "unknown" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
         print("Access Token is valid")
         exit(0)

    if args.default_account_id:
         # Set default Account_id
         print_deb("Set Default Acccount: {0}".format(args.default_account_id))
         accounts_info=netapp_api_cloud.occm_set_default_account(API_TOKEN, API_CONFIG_FILE, args.default_account_id)
         if (accounts_info["status"] == "success"):
              accounts=json.loads(accounts_info["accounts"])
              for account in accounts:
                   if ( account["accountPublicId"] == accounts_info["default"] ):
                         print("Name:[{0}] account_id:[{1}] Default:[X]".format(account["accountName"], account["accountPublicId"],))
                   else:
                         print("Name:[{0}] account_id:[{1}] Default:[ ]".format(account["accountName"], account["accountPublicId"],))
         else:
              print("ERROR: {0}".format(accounts_info["message"]))
              exit(1)

except KeyboardInterrupt:
    print ("exit")
    exit(0)