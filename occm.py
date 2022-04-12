#####################################################################
# occm python script for NetApp Cloud Manager
#####################################################################
import netapp_api_cloud
import argparse
import getpass
import sys
import configparser
import json
import os

RELEASE='0.6.2'
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
parser.add_argument("--account-id", dest='account_id', help="select account ID")
parser.add_argument("--agent-id", dest='agent_id', help="select cloud manager Connector")
parser.add_argument("-j", "--json", dest='json', help="print in json format", action="store_true")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--account-list", dest='account_list', help="print accounts list", action="store_true" )
group.add_argument("--cloud-account-list", dest='cloud_account_list', help="print cloud accounts list", action="store_true" )
group.add_argument("--agent-list", dest='agent_list', help="print cloud manager connectors list", action="store_true" )
group.add_argument("--agent-switch", dest='switch_agent_id', help="switch to a connector using it agent_id" )
group.add_argument("--cvo-list", dest='list_cvo', help="list all Cloud Volumes ONTAP working environments", action="store_true" )
group.add_argument("--cvo-get", dest='get_cvo_id', help="get an existing Cloud Volumes ONTAP working environment details" )
group.add_argument("--cvo-get-creation-parameters", dest='get_cvo_id_creation_parameters', help="get an existing Cloud Volumes ONTAP creation parameters" )
group.add_argument("--cvo-start", dest='start_cvo_id', help="start an existing Cloud Volumes ONTAP working environment " )
group.add_argument("--cvo-stop", dest='stop_cvo_id', help="stop an existing Cloud Volumes ONTAP working environment" )
group.add_argument("--cvo-delete", dest='delete_cvo_id', help="delete an existing Cloud Volumes ONTAP working environment" )
group.add_argument("--cvo-az-create", dest='create_cvo_az_file', help="create a new Cloud Volumes ONTAP in Azure")
group.add_argument("--cvo-az-create-ha", dest='create_cvo_az_ha_file', help="create a new Cloud Volumes ONTAP HA in Azure")
group.add_argument("--cvo-az-delete-force", dest='delete_cvo_az_id', help="Force delete an existing Cloud Volumes ONTAP in Azure" )
group.add_argument("--cvo-az-delete-ha-force", dest='delete_cvo_az_ha_id', help="Force delete an existing Cloud Volumes ONTAP HA in Azure" )
group.add_argument("--cvo-aw-create", dest='create_cvo_aw_file', help="create a new Cloud Volumes ONTAP in AWS ")
group.add_argument("--cvo-aw-create-ha", dest='create_cvo_aw_ha_file', help="create a new Cloud Volumes ONTAP HA in AWS")
group.add_argument("--cvo-aw-delete-force", dest='delete_cvo_aw_id', help="Force delete an existing Cloud Volumes ONTAP in AWS" )
group.add_argument("--cvo-aw-delete-ha-force", dest='delete_cvo_aw_ha_id', help="Force delete an existing Cloud Volumes ONTAP HA in AWS" )
group.add_argument("--token-check", dest='check_token', help="check NetApp Cloud access token", action="store_true" )
group.add_argument("--token-get-new", dest='get_new_token', help="get a new access token", action="store_true" )

args = parser.parse_args()

if args.debug:
      Debug = True
      netapp_api_cloud.Debug = True 

try:
    file_info = netapp_api_cloud.check_API_config_file(API_CONFIG_FILE)
    if ( file_info["status"] != "success" ):
         print("ERROR: {0}".format(file_info["message"]))
         exit(1)

    if args.get_new_token:
         # Create a new token
         token_info=netapp_api_cloud.create_new_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
    else: 
         # Get Token and cloud manager account informations 
         print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)

    API_TOKEN=token_info["token"]

    print_deb("API_TOKEN: {0}".format(API_TOKEN))

    # Get Current Account_id from config file
    account_info=netapp_api_cloud.get_current_account(API_CONFIG_FILE)
    if (account_info["status"] == "success"):
         account_id = account_info["current_account_id"] 
    else:
         account_id = ""

    # Get Current Cloud Manager agent_id from config file
    agent_info=netapp_api_cloud.get_current_occm_agent(API_CONFIG_FILE)
    if (agent_info["status"] == "success"):
         agent_id = agent_info["current_agent_id"] 
    else:
         agent_id = ""

    # Arg --account-id ID
    if args.account_id:
         account_id = args.account_id 

    accountName = netapp_api_cloud.occm_get_accountName(API_TOKEN,account_id)
    if ( accountName == ""):
         print("ERRRO: Account {0} not found".format(account_id))
         exit(1)
    if ( accountName == "Demo_SIM"):
         print("ERROR: API not supported with Account [Demo_SIM] [{0}]".format(account_id))
         print("ERROR: Please switch to another Account")
         exit(1)
    
    # Arg --account-list: Print cloud central accounts 
    if args.account_list:
         current_account_id = account_id 
         print("Print NetApp Account list:")
         accounts_info=netapp_api_cloud.occm_get_accounts_list(API_TOKEN)
         print_deb(accounts_info)
         if (accounts_info["status"] == "success"):
              accounts=json.loads(accounts_info["accounts"])
              print("Print NetApp Account list[{0}]:".format(len(accounts)))
              if (args.json):
                   print(json.dumps(accounts, indent=4))
              else:
                   for account in accounts:
                        if ( account["accountPublicId"] == current_account_id ):
                             print("Name:[{0}] account_id:[{1}] Current:[X]".format(account["accountName"], account["accountPublicId"]))
                        else:
                             print("Name:[{0}] account_id:[{1}]".format(account["accountName"], account["accountPublicId"]))
         else:
              print("ERROR: {0}".format(accounts_info["message"]))
              exit(1)

    # Arg --agent-id ID 
    if args.agent_id:
         agent_id = args.agent_id 

    # Arg --cloud-account-list: Print cloud Account registered 
    if args.cloud_account_list:
         
         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if (agent_id == ""):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Print NetApp Cloud Account list:")
         accounts_info=netapp_api_cloud.occm_get_cloud_accounts_list(API_TOKEN,account_id,agent_id)
         print_deb(accounts_info)
         if (accounts_info["status"] == "success"):
              accounts=json.loads(accounts_info["accounts"])
              print("Print NetApp Account list[{0}]:".format(len(accounts)))
              if (args.json):
                   print(json.dumps(accounts, indent=4))
              else:
                   for providers_accounts in accounts:
                        provider="{0}".format(providers_accounts)
                        provider_accounts=accounts[provider]
                        count=len(provider_accounts)
                        if ( count == 0 ):
                             print("provider: [{0}] ".format(provider))
                        else:
                             for account in provider_accounts:
                                  print("provider:[{0}] Name:[{1}] ID:[{2}] Type[{3}]".format(provider,account["accountName"], account["publicId"], account["accountType"]))
         else:
              print("ERROR: {0}".format(accounts_info["message"]))
              exit(1)

    # Arg --connector-list: Print cloud Manager Agents list 
    if args.agent_list:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         current_agent_id = agent_id

         print("Print Cloud Manager Agents List")
         agents_info=netapp_api_cloud.occm_get_occms_list(API_TOKEN, account_id)
         print_deb(agents_info)
         if (agents_info["status"] == "success"):
              occms=json.loads(agents_info["occms"])
              agents=occms["occms"]
              print("Print NetApp OCCM Agent list[{0}]:".format(len(agents)))
              if (args.json):
                   print(json.dumps(agents, indent=4))
              else:
                   for agent in agents:
                       if ( agent["agent"]["agentId"] == current_agent_id ):
                            print("Name:[{0}] AgentID:[{1}] [{2}] [{3}] [{4}] Current [X]".format(agent["occmName"],agent["agent"]["agentId"],agent["primaryCallbackUri"],agent["agent"]["provider"],agent["agent"]["status"]))
                       else: 
                            print("Name:[{0}] AgentID:[{1}] [{2}] [{3}] [{4}]".format(agent["occmName"],agent["agent"]["agentId"],agent["primaryCallbackUri"],agent["agent"]["provider"],agent["agent"]["status"]))
         else:
              print("ERROR: {0}".format(agents_info["message"]))
              exit(1)

    # Arg --agent-switch: Switch to a Connector using Agent_id 
    if args.switch_agent_id:
         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         agents_info=netapp_api_cloud.set_current_occm_agent(API_TOKEN,API_CONFIG_FILE,account_id,args.switch_agent_id)
         if (agents_info["status"] == "success"):
              print("Set default occm agent to: [{0}]".format(args.switch_agent_id))
         else:
              print("ERROR: {0}".format(agents_info["message"]))
              exit(1)

    # Arg --cvo-list: Print Cloud Volumes ONTAP list
    if args.list_cvo:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         # List CVO Azure
         cvos_az_info=netapp_api_cloud.cvo_azure_get_vsa_list(API_TOKEN, account_id, agent_id )
         print_deb(cvos_az_info)
         if (cvos_az_info["status"] == "success"):
              cvos_az=json.loads(cvos_az_info["cvos"])
              if ( len(cvos_az) > 0 ):
                   print("Print Azure Cloud Volume ONTAP list[{0}]:".format(len(cvos_az)))
                   if (args.json):
                        print(json.dumps(cvos_az, indent=4))
                   else:
                       for cvo in cvos_az:
                            print("Name:[{0}][{1}] id:[{2}] HA:[{3}] status[{4}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"]))
         else:
              print("ERROR: {0}".format(cvos_az_info["message"]))
              exit(1)

         # List CVO AWS 
         cvos_az_info=netapp_api_cloud.cvo_aws_get_vsa_list(API_TOKEN, account_id, agent_id )
         print_deb(cvos_az_info)
         if (cvos_az_info["status"] == "success"):
              cvos_az=json.loads(cvos_az_info["cvos"])
              if ( len(cvos_az) > 0 ):
                   print("Print AWS Cloud Volume ONTAP list[{0}]:".format(len(cvos_az)))
                   if (args.json):
                        print(json.dumps(cvos_az, indent=4))
                   else:
                       for cvo in cvos_az:
                            print("Name:[{0}][{1}] id:[{2}] HA:[{3}] status[{4}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"]))
         else:
              print("ERROR: {0}".format(cvos_az_info["message"]))
              exit(1)


    # Arg --cvo-get: Print details of Cloud Volumes ONTAP working environment
    if args.get_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Print details of Cloud Volumes ONTAP working environment ID: {0}".format(args.get_cvo_id))

         cvo_info=netapp_api_cloud.cvo_get_working_environment(API_TOKEN, account_id, agent_id,args.get_cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {0}".format(isHA))
              print_deb("cloudProvierName: {0}".format(cloudProviderName))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

         # Cloud Provider Azure
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.get_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        cvo_nodes=cvo["ontapClusterProperties"]["nodes"]
                        cvo_mgmt_ip = "" 
                        for cvo_node in cvo_nodes:
                             cvo_lifs = cvo_node["lifs"]
                             for cvo_lif in cvo_lifs:
                                  if (cvo_lif["lifType"] == "Cluster Management"):
                                      cvo_mgmt_ip = cvo_lif["ip"] 
                        print("Name:[{0}][{1}] HA:[{2}] svm:[{3}] status[{4}] mgmt[{5}]".format(cvo["name"],cvo["cloudProviderName"],cvo["isHA"],cvo["svmName"],cvo["status"]["status"],cvo_mgmt_ip))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         # Cloud Provider Amazon 
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.get_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        cvo_nodes=cvo["ontapClusterProperties"]["nodes"]
                        cvo_mgmt_ip = "" 
                        for cvo_node in cvo_nodes:
                             cvo_lifs = cvo_node["lifs"]
                             for cvo_lif in cvo_lifs:
                                  if (cvo_lif["lifType"] == "Cluster Management"):
                                      cvo_mgmt_ip = cvo_lif["ip"] 
                        print("Name:[{0}][{1}] HA:[{2}] svm:[{3}] status[{4}] mgmt[{5}]".format(cvo["name"],cvo["cloudProviderName"],cvo["isHA"],cvo["svmName"],cvo["status"]["status"],cvo_mgmt_ip))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)


         print("ERROR: cloud provider  [{0}] is not supported".format(cloudProviderName))

    # Arg --cvo_get_creation_parameters: Print details of Cloud Volumes ONTAP creation parameters 
    if args.get_cvo_id_creation_parameters:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         cvo_info=netapp_api_cloud.cvo_get_working_environment(API_TOKEN, account_id, agent_id,args.get_cvo_id_creation_parameters)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {0}".format(isHA))
              print_deb("cloudProvierName: {0}".format(cloudProviderName))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

         # Cloud Provider Azure
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa_creation_parameters(API_TOKEN, account_id, agent_id, isHA, args.get_cvo_id_creation_parameters)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   print(json.dumps(cvo["parameters"], indent=4))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         # Cloud Provider Amazon 
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa_creation_parameters(API_TOKEN, account_id, agent_id, isHA, args.get_cvo_id_creation_parameters)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   print(json.dumps(cvo["parameters"], indent=4))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{0}] is not supported".format(cloudProviderName))

    # Arg --cvo-start: Start an Cloud Volumes ONTAP working environment
    if args.start_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Start Cloud volumes ONTAP working environment ID: {0}".format(args.start_cvo_id))

         cvo_info=netapp_api_cloud.cvo_get_working_environment(API_TOKEN, account_id, agent_id,args.start_cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {0}".format(isHA))
              print_deb("cloudProvierName: {0}".format(cloudProviderName))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

         # Azure Cloud Provider
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.start_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{0}] id:[{1}] HA:[{2}] status:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)
         
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('Do you want to start CVO [{0}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_azure_action_vsa(API_TOKEN, account_id, agent_id, args.start_cvo_id, isHA, "start")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{0}] started".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         # AWS Cloud Provider
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.start_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{0}] id:[{1}] HA:[{2}] status:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)
         
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('Do you want to start CVO [{0}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_aws_action_vsa(API_TOKEN, account_id, agent_id, args.start_cvo_id, isHA, "start")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{0}] started".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{0}] is not supported".format(cloudProviderName))

    # Arg --cvo-stop: Stop a Cloud Volumes ONTAP working environment
    if args.stop_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Stop Cloud volumes ONTAP working environment ID: {0}".format(args.stop_cvo_id))

         cvo_info=netapp_api_cloud.cvo_get_working_environment(API_TOKEN, account_id, agent_id,args.stop_cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {0}".format(isHA))
              print_deb("cloudProvierName: {0}".format(cloudProviderName))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

         # Azure Cloud Provider
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.stop_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{0}] id:[{1}] HA:[{2}] status:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)
         
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to stop CVO [{0}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_azure_action_vsa(API_TOKEN, account_id, agent_id, args.stop_cvo_id, isHA, "stop")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{0}] stopped".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         # AWS Cloud Provider
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.stop_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{0}] id:[{1}] HA:[{2}] status:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)
         
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to stop CVO [{0}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_aws_action_vsa(API_TOKEN, account_id, agent_id, args.stop_cvo_id, isHA, "stop")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{0}] stopped".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{0}] is not supported".format(cloudProviderName))


    # Arg --cvo-stop: Delete a Cloud Volumes ONTAP working environment
    if args.delete_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Delete cloud volumes ONTAP working environment ID: {0}".format(args.delete_cvo_id))

         cvo_info=netapp_api_cloud.cvo_get_working_environment(API_TOKEN, account_id, agent_id,args.delete_cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {0}".format(isHA))
              print_deb("cloudProvierName: {0}".format(cloudProviderName))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

         # Azure Cloud Provider
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{0}] id:[{1}] HA:[{2}] svm:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)
         
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to delete the CVO [{0}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_azure_delete_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{0}] deleted".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         # AWS Cloud Provider
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{0}] id:[{1}] HA:[{2}] svm:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)
         
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to delete the CVO [{0}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_aws_delete_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{0}] deleted".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {0}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{0}] is not supported".format(cloudProviderName))


    # Arg --cvo-az-create: Create a new Cloud Volumes ONTAP in Azure 
    if args.create_cvo_az_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP in Azure")

         print_deb("Create new CVO using file: {0}".format(args.create_cvo_az_file))
         if (os.path.isfile(args.create_cvo_az_file) != True ):
              print("Error: {0} : file not found".format(args.create_cvo_az_file))
              exit(1)
         f = open(args.create_cvo_az_file)
         new_cvo_json=json.load(f)
         print_deb(new_cvo_json)
         f.close

         isHA = False
         cvo_info=netapp_api_cloud.cvo_azure_create_new(API_TOKEN, account_id, agent_id, isHA, new_cvo_json)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              if (args.json):
                   print(json.dumps(cvo, indent=4))
              else:
                   print("Name:[{0}] id:[{1}] HA:[{2}] svm:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)


    # Arg --cvo-az-create-ha: Create a new Cloud Volumes ONTAP HA in Azure 
    if args.create_cvo_az_ha_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP HA in Azure")

         print_deb("Create new CVO using file: {0}".format(args.create_cvo_az_ha_file))
         if (os.path.isfile(args.create_cvo_az_ha_file) != True ):
              print("Error: {0} : file not found".format(args.create_cvo_az_ha_file))
              exit(1)
         f = open(args.create_cvo_az_ha_file)
         new_cvo_json=json.load(f)
         print_deb(new_cvo_json)
         f.close

         isHA = True 
         cvo_info=netapp_api_cloud.cvo_azure_create_new(API_TOKEN, account_id, agent_id, isHA, new_cvo_json)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              if (args.json):
                   print(json.dumps(cvo, indent=4))
              else:
                   print("Name:[{0}] id:[{1}] HA:[{2}] svm:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

    # Arg --cvo-az-delete-force: Delete a Cloud Volumes ONTAP in Azure 
    if args.delete_cvo_az_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Delete Azure cloud volumes ONTAP working environment ID: {0}".format(args.delete_cvo_az_id))

         answer = ''
         while ( answer != "y" and answer != "n" ):
              answer=input('WARNING: do you want to delete the CVO ID [{0}] ? [y/n] : '.format(args.delete_cvo_az_id))

         if ( answer != "y"):
              exit(0)

         isHA = False
         cvo_info=netapp_api_cloud.cvo_azure_delete_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_az_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              print("CVO Name:[{0}] deleted".format(args.delete_cvo_az_id))
              exit(0)
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

    # Arg --cvo-az-delete-ha-force: Delete a Cloud Volumes ONTAP HA in Azure 
    if args.delete_cvo_az_ha_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Delete Azure cloud volumes ONTAP working environment ID: {0}".format(args.delete_cvo_az_ha_id))

         answer = ''
         while ( answer != "y" and answer != "n" ):
              answer=input('WARNING: do you want to delete the CVO ID [{0}] ? [y/n] : '.format(args.delete_cvo_az_ha_id))

         if ( answer != "y"):
              exit(0)

         isHA = True 
         cvo_info=netapp_api_cloud.cvo_azure_delete_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_az_ha_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              print("CVO Name:[{0}] deleted".format(args.delete_cvo_az_ha_id))
              exit(0)
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)


    # Arg --cvo-aw-create: Create a new Cloud Volumes ONTAP in AWS 
    if args.create_cvo_aw_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP in AWS")

         print_deb("Create new CVO using file: {0}".format(args.create_cvo_aw_file))
         if (os.path.isfile(args.create_cvo_aw_file) != True ):
              print("Error: {0} : file not found".format(args.create_cvo_aw_file))
              exit(1)
         f = open(args.create_cvo_aw_file)
         new_cvo_json=json.load(f)
         print_deb(new_cvo_json)
         f.close

         isHA = False
         cvo_info=netapp_api_cloud.cvo_aws_create_new(API_TOKEN, account_id, agent_id, isHA, new_cvo_json)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              if (args.json):
                   print(json.dumps(cvo, indent=4))
              else:
                   print("Name:[{0}] id:[{1}] HA:[{2}] svm:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)


    # Arg --cvo-aw-create-ha: Create a new Cloud Volumes ONTAP HA in AWS 
    if args.create_cvo_aw_ha_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP HA in AWS")

         print_deb("Create new CVO using file: {0}".format(args.create_cvo_aw_ha_file))
         if (os.path.isfile(args.create_cvo_aw_ha_file) != True ):
              print("Error: {0} : file not found".format(args.create_cvo_aw_ha_file))
              exit(1)
         f = open(args.create_cvo_aw_ha_file)
         new_cvo_json=json.load(f)
         print_deb(new_cvo_json)
         f.close

         isHA = True 
         cvo_info=netapp_api_cloud.cvo_aws_create_new(API_TOKEN, account_id, agent_id, isHA, new_cvo_json)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              if (args.json):
                   print(json.dumps(cvo, indent=4))
              else:
                   print("Name:[{0}] id:[{1}] HA:[{2}] svm:[{3}] provider[{4}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

    # Arg --cvo-delete-aw-force: Delete a Cloud Volumes ONTAP in AWS 
    if args.delete_cvo_aw_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Delete AWS cloud volumes ONTAP working environment ID: {0}".format(args.delete_cvo_aw_id))

         answer = ''
         while ( answer != "y" and answer != "n" ):
              answer=input('WARNING: do you want to delete the CVO ID [{0}] ? [y/n] : '.format(args.delete_cvo_aw_id))

         if ( answer != "y"):
              exit(0)

         isHA = False
         cvo_info=netapp_api_cloud.cvo_aws_delete_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_aw_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              print("CVO Name:[{0}] deleted".format(args.delete_cvo_aw_id))
              exit(0)
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)

    # Arg --cvo-delete-aw-ha-force: Delete a Cloud Volumes ONTAP HA in AWS 
    if args.delete_cvo_aw_ha_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Delete AWS cloud volumes ONTAP working environment ID: {0}".format(args.delete_cvo_aw_ha_id))

         answer = ''
         while ( answer != "y" and answer != "n" ):
              answer=input('WARNING: do you want to delete the CVO ID [{0}] ? [y/n] : '.format(args.delete_cvo_aw_ha_id))

         if ( answer != "y"):
              exit(0)

         isHA = True 
         cvo_info=netapp_api_cloud.cvo_aws_delete_vsa(API_TOKEN, account_id, agent_id, isHA, args.delete_cvo_aw_ha_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              print("CVO Name:[{0}] deleted".format(args.delete_cvo_aw_ha_id))
              exit(0)
         else:
              print("ERROR: {0}".format(cvo_info["message"]))
              exit(1)



    # Arg --check-token: Check if API token is still valid 
    if args.check_token:
         # Get Token and cloud manager account informations 
         print_deb("API Configuration File: {0}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] == "unknown" ):
              print("ERROR: {0}".format(token_info["message"]))
              exit(1)
         print("Access Token is valid")
         exit(0)

except KeyboardInterrupt:
    print ("exit")
    exit(0)
