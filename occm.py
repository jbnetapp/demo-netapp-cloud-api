#####################################################################
# occm python script for NetApp Cloud Manager
# Jerome.Blanchet@NetApp.com
#####################################################################
import netapp_api_cloud
import argparse
import getpass
import sys
import configparser
import json
import os

RELEASE='0.6.4'
#####################################################################
# Local API
#####################################################################
Debug = False
Verbose = False

def print_vers():
      print (RELEASE)

def print_syntax_error(mess):
      print ('ERROR: {}'.format(mess))

def print_deb (debug_var):
    if (Debug):
        print("DEBUG: [", end="")
        print(debug_var,end="]\n")

def print_verb (mess):
    if (Verbose):
        print(mess)

def get_cvo_id_byname(cvo_name_or_id):
    if ( account_id == "" ):
         print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
         exit(1)

    if ( agent_id == "" ):
         print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
         exit(1)

    # List CVO Azure
    we_info=netapp_api_cloud.occm_get_working_environments_list(API_TOKEN, account_id, agent_id )
    print_deb(we_info)
    if (we_info["status"] == "success"):
         we_list=json.loads(we_info["working-environments"])
         cvos_aws=we_list["vsaWorkingEnvironments"]
         cvos_az=we_list["azureVsaWorkingEnvironments"]
         cvos_gcp=we_list["gcpVsaWorkingEnvironments"]
         if ( len(cvos_aws) > 0 ):
              for cvo in cvos_aws:
                   print_deb("Name:[{}][{}]".format(cvo["name"],cvo["publicId"]))
                   if ((cvo["name"] == cvo_name_or_id) or (cvo["publicId"] == cvo_name_or_id)):
                        return cvo["publicId"]
         if ( len(cvos_az) > 0 ):
              for cvo in cvos_az:
                   print_deb("Name:[{}][{}]".format(cvo["name"],cvo["publicId"]))
                   if ((cvo["name"] == cvo_name_or_id) or (cvo["publicId"] == cvo_name_or_id)):
                        return cvo["publicId"]
         if ( len(cvos_gcp) > 0 ):
              for cvo in cvos_gcp:
                   print_deb("Name:[{}][{}]".format(cvo["name"],cvo["publicId"]))
                   if ((cvo["name"] == cvo_name_or_id) or (cvo["publicId"] == cvo_name_or_id)):
                        return cvo["publicId"]
         return None
    else:
         print("ERROR: {}".format(we_info["message"]))
         return None

def print_cvo_from_json(cvo):
    cvo_name=cvo["name"]
    cvo_nodes=cvo["ontapClusterProperties"]["nodes"]
    cvo_mgmt_ip = ""
    node_number = 1
    # nodes information
    for cvo_node in cvo_nodes:
         cvo_node_name = cvo_node["name"]
         cvo_node_serial = cvo_node["serialNumber"]
         cvo_node_sysid = cvo_node["systemId"]
         print_verb("Name:[{}][{}] node{}:[{}][{}][{}]".format(cvo["name"],cvo["cloudProviderName"],node_number,cvo_node_name,cvo_node_serial,cvo_node_sysid))
         cvo_lifs = cvo_node["lifs"]
         for cvo_lif in cvo_lifs:
              if (cvo_lif["lifType"] == "Cluster Management"):
                   cvo_mgmt_ip = cvo_lif["ip"]
              if (cvo_lif["lifType"] == "Data"):
                   print_verb("Name:[{}][{}] node{}_lif:[{}][{}][{}]".format(cvo["name"],cvo["cloudProviderName"],node_number,cvo_lif["lifType"],cvo_lif["ip"],cvo_lif["dataProtocols"]))
              else:
                   print_verb("Name:[{}][{}] node{}_lif:[{}][{}]".format(cvo["name"],cvo["cloudProviderName"],node_number,cvo_lif["lifType"],cvo_lif["ip"],))
         node_number += 1

    if (Verbose == False ):
         print("Name:[{}][{}] id:[{}] HA:[{}] status:[{}] mgmt:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo_mgmt_ip))
    else:
         # cluster information
         print_verb("Name:[{}][{}] ontap_version:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["ontapClusterProperties"]["ontapVersion"]))
         print_verb("Name:[{}][{}] license_name:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["ontapClusterProperties"]["licensePackageName"]))
         print_verb("Name:[{}][{}] mgmt_ip:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo_mgmt_ip))
         print_verb("Name:[{}][{}] svm_name:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["svmName"]))
         print_verb("Name:[{}][{}] status:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["status"]["status"]))
         if (cvo["isHA"] == True):
              print_verb("Name:[{}][{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["isHA"]))
              if (cvo["cloudProviderName"] == "Azure" ):
                   cvo_resourcegroup=""
                   if (cvo["providerProperties"]["resourceGroup"] is not None) :
                        cvo_resourcegroup=cvo["providerProperties"]["resourceGroup"]["name"]
                   cvo_loadbalancer=cvo["haProperties"]["loadBalancerName"]
                   cvo_multizone=cvo["haProperties"]["multiZone"]
                   print_verb("Name:[{}][{}] loadBalancer:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo_loadbalancer))
                   print_verb("Name:[{}][{}] resourceGroup:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo_resourcegroup))
                   print_verb("Name:[{}][{}] multiZone:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo_multizone))
         print_verb("")

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
parser.add_argument("-v", "--verbose", dest='verbose', help="verbose mode", action="store_true")
parser.add_argument("-s", "--status", dest='status', help="display cvo status", action="store_true")
parser.add_argument("--account-id", dest='account_id', help="select account ID")
parser.add_argument("--agent-id", dest='agent_id', help="select cloud manager Connector")
parser.add_argument("-j", "--json", dest='json', help="print in json format", action="store_true")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--account-list", dest='account_list', help="print accounts list", action="store_true" )
group.add_argument("--cloud-account-list", dest='cloud_account_list', help="print cloud accounts list", action="store_true" )
group.add_argument("--agent-list", dest='agent_list', help="print cloud manager connectors list", action="store_true" )
group.add_argument("--agent-switch", dest='switch_agent_id', help="switch to a connector using it agent_id" )
group.add_argument("--we-list", dest='list_we', help="list all working environments", action="store_true" )
group.add_argument("--cvo-list", dest='list_cvo', help="list all Cloud Volumes ONTAP working environments", action="store_true" )
group.add_argument("--cvo-get", dest='get_cvo_id', help="get an existing Cloud Volumes ONTAP working environment details" )
group.add_argument("--cvo-get-creation-parameters", dest='get_cvo_id_creation_parameters', help="get an existing Cloud Volumes ONTAP creation parameters" )
group.add_argument("--cvo-start", dest='start_cvo_id', help="start an existing Cloud Volumes ONTAP working environment " )
group.add_argument("--cvo-stop", dest='stop_cvo_id', help="stop an existing Cloud Volumes ONTAP working environment" )
group.add_argument("--cvo-delete", dest='delete_cvo_id', help="delete an existing Cloud Volumes ONTAP working environment" )
group.add_argument("--cvo-az-create", dest='create_cvo_az_file', help="create a new Cloud Volumes ONTAP in Azure")
group.add_argument("--cvo-az-create-ha", dest='create_cvo_az_ha_file', help="create a new Cloud Volumes ONTAP HA in Azure")
group.add_argument("--cvo-aws-create", dest='create_cvo_aws_file', help="create a new Cloud Volumes ONTAP in AWS ")
group.add_argument("--cvo-aws-create-ha", dest='create_cvo_aws_ha_file', help="create a new Cloud Volumes ONTAP HA in AWS")
group.add_argument("--cvo-gcp-create", dest='create_cvo_gcp_file', help="create a new Cloud Volumes ONTAP in GCP ")
group.add_argument("--cvo-gcp-create-ha", dest='create_cvo_gcp_ha_file', help="create a new Cloud Volumes ONTAP HA in GCP")
group.add_argument("--token-check", dest='check_token', help="check NetApp Cloud access token", action="store_true" )
group.add_argument("--token-get-new", dest='get_new_token', help="get a new access token", action="store_true" )
group.add_argument("--version", dest='version', help="print release", action="store_true" )

args = parser.parse_args()

if args.debug:
      Debug = True
      netapp_api_cloud.Debug = True

if args.verbose:
      Verbose = True

if args.status:
      Status = True
try:
    file_info = netapp_api_cloud.check_API_config_file(API_CONFIG_FILE)
    if ( file_info["status"] != "success" ):
         print("ERROR: {}".format(file_info["message"]))
         exit(1)

    if args.get_new_token:
         # Create a new token
         token_info=netapp_api_cloud.create_new_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {}".format(token_info["message"]))
              exit(1)
    else:
         # Get Token and cloud manager account informations
         print_deb("API Configuration File: {}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] != "success" ):
              print("ERROR: {}".format(token_info["message"]))
              exit(1)

    API_TOKEN=token_info["token"]

    print_deb("API_TOKEN: {}".format(API_TOKEN))

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
         print("ERRRO: Account {} not found".format(account_id))
         exit(1)
    if ( accountName == "Demo_SIM"):
         print("ERROR: API not supported with Account [Demo_SIM] [{}]".format(account_id))
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
              print("Print NetApp Account list[{}]:".format(len(accounts)))
              if (args.json):
                   print(json.dumps(accounts, indent=4))
              else:
                   for account in accounts:
                        if ( account["accountPublicId"] == current_account_id ):
                             print("Name:[{}] account_id:[{}] Current:[X]".format(account["accountName"], account["accountPublicId"]))
                        else:
                             print("Name:[{}] account_id:[{}]".format(account["accountName"], account["accountPublicId"]))
         else:
              print("ERROR: {}".format(accounts_info["message"]))
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
              print("Print NetApp Account list[{}]:".format(len(accounts)))
              if (args.json):
                   print(json.dumps(accounts, indent=4))
              else:
                   for providers_accounts in accounts:
                        provider="{}".format(providers_accounts)
                        provider_accounts=accounts[provider]
                        count=len(provider_accounts)
                        if ( count == 0 ):
                             print("provider: [{}] ".format(provider))
                        else:
                             for account in provider_accounts:
                                  print("provider:[{}] Name:[{}] ID:[{}] Type:[{}]".format(provider,account["accountName"], account["publicId"], account["accountType"]))
         else:
              print("ERROR: {}".format(accounts_info["message"]))
              exit(1)

    # Arg --connector-list: Print cloud Manager Agents list
    if args.agent_list:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         current_agent_id = agent_id

         agents_info=netapp_api_cloud.occm_get_occms_list(API_TOKEN, account_id)
         print_deb(agents_info)
         if (agents_info["status"] == "success"):
              occms=json.loads(agents_info["occms"])
              agents=occms["occms"]
              print("Print NetApp OCCM Agent list[{}]:".format(len(agents)))
              if (args.json):
                   print(json.dumps(agents, indent=4))
              else:
                   for agent in agents:
                       if ( agent["status"] == "active" ):
                            if ( agent["agent"]["agentId"] == current_agent_id ):
                                print("Name:[{}] AgentID:[{}] [{}] [{}] [{}] Current [X]".format(agent["agent"]["name"],agent["agent"]["agentId"],agent["primaryCallbackUri"],agent["agent"]["provider"],agent["agent"]["status"]))
                            else:
                                print("Name:[{}] AgentID:[{}] [{}] [{}] [{}]".format(agent["agent"]["name"],agent["agent"]["agentId"],agent["primaryCallbackUri"],agent["agent"]["provider"],agent["agent"]["status"]))
                       else:
                                print("Name:[{}] AgentID:[{}] [{}]".format(agent["agent"]["name"],agent["agent"]["agentId"],agent["status"]))
         else:
              print("ERROR: {}".format(agents_info["message"]))
              exit(1)

    # Arg --agent-switch: Switch to a Connector using Agent_id
    if args.switch_agent_id:
         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         agents_info=netapp_api_cloud.set_current_occm_agent(API_TOKEN,API_CONFIG_FILE,account_id,args.switch_agent_id)
         if (agents_info["status"] == "success"):
              print("Set default occm agent to: [{}]".format(args.switch_agent_id))
         else:
              print("ERROR: {}".format(agents_info["message"]))
              exit(1)

    # Arg --we-list: Print Working Environment list
    if args.list_we:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         # Get BlueXP Working environmens list
         we_info=netapp_api_cloud.occm_get_working_environments_list(API_TOKEN, account_id, agent_id )
         print_deb(we_info)
         if (we_info["status"] == "success"):
              we_list=json.loads(we_info["working-environments"])
              if (args.json):
                   print(json.dumps(we_list, indent=4))
              else:
                   onPrems=we_list["onPremWorkingEnvironments"]
                   cvos_aws=we_list["vsaWorkingEnvironments"]
                   cvos_az=we_list["azureVsaWorkingEnvironments"]
                   cvos_gcp=we_list["gcpVsaWorkingEnvironments"]
                   if ( len(onPrems) > 0 ):
                        for ontap in onPrems:
                             print("Name:[{}][{}]".format(ontap["name"],ontap["publicId"]))
                   if ( len(cvos_aws) > 0 ):
                        for cvo in cvos_aws:
                             print("Name:[{}][{}]".format(cvo["name"],cvo["publicId"]))
                   if ( len(cvos_az) > 0 ):
                        for cvo in cvos_az:
                             print("Name:[{}][{}]".format(cvo["name"],cvo["publicId"]))
                   if ( len(cvos_gcp) > 0 ):
                        for cvo in cvos_gcp:
                             print("Name:[{}][{}]".format(cvo["name"],cvo["publicId"]))
         else:
              print("ERROR: {}".format(we_info["message"]))
              exit(1)

    # Arg --cvo-list: Print Cloud Volumes ONTAP list
    if args.list_cvo:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         # Get BlueXP Working environmens list
         we_info=netapp_api_cloud.occm_get_working_environments_list(API_TOKEN, account_id, agent_id )
         print_deb(we_info)
         if (we_info["status"] == "success"):
              we_list=json.loads(we_info["working-environments"])
              if (args.json):
                   print(json.dumps(we_list, indent=4))
              else:
                   cvos_aws=we_list["vsaWorkingEnvironments"]
                   cvos_az=we_list["azureVsaWorkingEnvironments"]
                   cvos_gcp=we_list["gcpVsaWorkingEnvironments"]
                   if ( len(cvos_aws) > 0 ):
                        for cvo in cvos_aws:
                             if (args.status):
                                  isHA=cvo["isHA"]
                                  cvo_id=cvo["publicId"]
                                  cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
                                  print_deb(cvo_info)
                                  if (cvo_info["status"] == "success"):
                                       cvo_status=json.loads(cvo_info["cvo"])
                                       if (args.json):
                                            print(json.dumps(cvo_status, indent=4))
                                       else:
                                            print_cvo_from_json(cvo_status)
                                  else:
                                       print("Name:[{}][{}] id:[{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"]))
                                       print("ERROR: {}".format(cvo_info["message"]))
                             else:
                                  print("Name:[{}][{}] id:[{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"]))

                   if ( len(cvos_az) > 0 ):
                        for cvo in cvos_az:
                             if (args.status):
                                  isHA=cvo["isHA"]
                                  cvo_id=cvo["publicId"]
                                  cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
                                  print_deb(cvo_info)
                                  if (cvo_info["status"] == "success"):
                                       cvo_status=json.loads(cvo_info["cvo"])
                                       if (args.json):
                                            print(json.dumps(cvo_status, indent=4))
                                       else:
                                            print_cvo_from_json(cvo_status)
                                  else:
                                       print("Name:[{}][{}] id:[{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"]))
                                       print("ERROR: {}".format(cvo_info["message"]))
                             else:
                                  print("Name:[{}][{}] id:[{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"]))

                   if ( len(cvos_gcp) > 0 ):
                        for cvo in cvos_gcp:
                             if (args.status):
                                  isHA=cvo["isHA"]
                                  cvo_id=cvo["publicId"]
                                  cvo_info=netapp_api_cloud.cvo_gcp_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
                                  print_deb(cvo_info)
                                  if (cvo_info["status"] == "success"):
                                       cvo_status=json.loads(cvo_info["cvo"])
                                       if (args.json):
                                            print(json.dumps(cvo_status, indent=4))
                                       else:
                                            print_cvo_from_json(cvo_status)
                                  else:
                                       print("Name:[{}][{}] id:[{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"]))
                                       print("ERROR: {}".format(cvo_info["message"]))
                             else:
                                  print("Name:[{}][{}] id:[{}] HA:[{}]".format(cvo["name"],cvo["cloudProviderName"],cvo["publicId"],cvo["isHA"]))

         else:
              print("ERROR: {}".format(we_info["message"]))
              exit(1)

    # Arg --cvo-get: Print details of Cloud Volumes ONTAP working environment
    if args.get_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         cvo_id=get_cvo_id_byname(args.get_cvo_id)
         if (cvo_id is None):
               print("Error: [{}] not found".format(args.get_cvo_id))
               exit(1)
         print_deb(cvo_id)

         cvo_info=netapp_api_cloud.occm_get_working_environment(API_TOKEN, account_id, agent_id,cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {}".format(isHA))
              print_deb("cloudProvierName: {}".format(cloudProviderName))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

         # Cloud Provider Azure
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        print_cvo_from_json(cvo)
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # Cloud Provider Amazon
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        print_cvo_from_json(cvo)
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # Cloud Provider GCP
         if (cloudProviderName == "GCP"):
              cvo_info=netapp_api_cloud.cvo_gcp_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        print_cvo_from_json(cvo)
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{}] is not supported".format(cloudProviderName))

    # Arg --cvo_get_creation_parameters: Print details of Cloud Volumes ONTAP creation parameters
    if args.get_cvo_id_creation_parameters:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         cvo_id=get_cvo_id_byname(args.get_cvo_id_creation_parameters)
         if (cvo_id is None):
               print("Error: [{}] not found".format(args.get_cvo_id_creation_parameters))
               exit(1)
         print_deb(cvo_id)

         cvo_info=netapp_api_cloud.occm_get_working_environment(API_TOKEN, account_id, agent_id, cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {}".format(isHA))
              print_deb("cloudProvierName: {}".format(cloudProviderName))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

         # Cloud Provider Azure
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa_creation_parameters(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   print(json.dumps(cvo["parameters"], indent=4))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # Cloud Provider Amazon
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa_creation_parameters(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   print(json.dumps(cvo["parameters"], indent=4))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # Cloud Provider  GCP
         if (cloudProviderName == "GCP"):
              cvo_info=netapp_api_cloud.cvo_gcp_get_vsa_creation_parameters(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   print(json.dumps(cvo["parameters"], indent=4))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{}] is not supported".format(cloudProviderName))

    # Arg --cvo-start: Start an Cloud Volumes ONTAP working environment
    if args.start_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         cvo_id=get_cvo_id_byname(args.start_cvo_id)
         if (cvo_id is None):
               print("Error: [{}] not found".format(args.start_cvo_id))
               exit(1)
         print_deb(cvo_id)


         print("Start Cloud volumes ONTAP working environment ID: {}".format(cvo_id))

         cvo_info=netapp_api_cloud.occm_get_working_environment(API_TOKEN, account_id, agent_id, cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {}".format(isHA))
              print_deb("cloudProvierName: {}".format(cloudProviderName))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

         # Azure Cloud Provider
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] status:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('Do you want to start CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_azure_action_vsa(API_TOKEN, account_id, agent_id, cvo_id, isHA, "start")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] started".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # AWS Cloud Provider
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] status:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)
 
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('Do you want to start CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_aws_action_vsa(API_TOKEN, account_id, agent_id, cvo_id, isHA, "start")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] started".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # GCP Cloud Provider
         if (cloudProviderName == "GCP"):
              cvo_info=netapp_api_cloud.cvo_gcp_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] status:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('Do you want to start CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_gcp_action_vsa(API_TOKEN, account_id, agent_id, cvo_id, isHA, "start")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] started".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{}] is not supported".format(cloudProviderName))

    # Arg --cvo-stop: Stop a Cloud Volumes ONTAP working environment
    if args.stop_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         cvo_id=get_cvo_id_byname(args.stop_cvo_id)
         if (cvo_id is None):
               print("Error: [{}] not found".format(args.stop_cvo_id))
               exit(1)
         print_deb(cvo_id)

         print("Stop Cloud volumes ONTAP working environment ID: {}".format(cvo_id))

         cvo_info=netapp_api_cloud.occm_get_working_environment(API_TOKEN, account_id, agent_id, cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {}".format(isHA))
              print_deb("cloudProvierName: {}".format(cloudProviderName))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

         # Azure Cloud Provider
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] status:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)
 
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to stop CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_azure_action_vsa(API_TOKEN, account_id, agent_id, cvo_id, isHA, "stop")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] stopped".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # AWS Cloud Provider
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] status:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)
 
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to stop CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_aws_action_vsa(API_TOKEN, account_id, agent_id, cvo_id, isHA, "stop")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] stopped".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # GCP  Cloud Provider
         if (cloudProviderName == "GCP"):
              cvo_info=netapp_api_cloud.cvo_gcp_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] status:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["status"]["status"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)
 
              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to stop CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_gcp_action_vsa(API_TOKEN, account_id, agent_id, cvo_id, isHA, "stop")
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] stopped".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{}] is not supported".format(cloudProviderName))


    # Arg --cvo-delete: Delete a Cloud Volumes ONTAP working environment
    if args.delete_cvo_id:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         cvo_id=get_cvo_id_byname(args.delete_cvo_id)
         if (cvo_id is None):
               print("Error: [{}] not found".format(args.delete_cvo_id))
               exit(1)
         print_deb(cvo_id)

         print("Delete cloud volumes ONTAP working environment ID: {}".format(cvo_id))

         cvo_info=netapp_api_cloud.occm_get_working_environment(API_TOKEN, account_id, agent_id, cvo_id)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              isHA=cvo["isHA"]
              cloudProviderName=cvo["cloudProviderName"]
              print_deb("isHA: {}".format(isHA))
              print_deb("cloudProvierName: {}".format(cloudProviderName))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

         # Azure Cloud Provider
         if (cloudProviderName == "Azure"):
              cvo_info=netapp_api_cloud.cvo_azure_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to delete the CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_azure_delete_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] deleted".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # AWS Cloud Provider
         if (cloudProviderName == "Amazon"):
              cvo_info=netapp_api_cloud.cvo_aws_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to delete the CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_aws_delete_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] deleted".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         # GCP Cloud Provider
         if (cloudProviderName == "GCP"):
              cvo_info=netapp_api_cloud.cvo_gcp_get_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   cvo=json.loads(cvo_info["cvo"])
                   if (args.json):
                        print(json.dumps(cvo, indent=4))
                   else:
                        cvo_name=cvo["name"]
                        print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

              answer = ''
              while ( answer != "y" and answer != "n" ):
                   answer=input('WARNING: do you want to delete the CVO [{}] ? [y/n] : '.format(cvo["name"]))

              if ( answer != "y"):
                   exit(0)

              cvo_info=netapp_api_cloud.cvo_gcp_delete_vsa(API_TOKEN, account_id, agent_id, isHA, cvo_id)
              print_deb(cvo_info)
              if (cvo_info["status"] == "success"):
                   print("CVO Name:[{}] deleted".format(cvo_name))
                   exit(0)
              else:
                   print("ERROR: {}".format(cvo_info["message"]))
                   exit(1)

         print("ERROR: cloud provider  [{}] is not supported".format(cloudProviderName))

    # Arg --cvo-az-create: Create a new Cloud Volumes ONTAP in Azure
    if args.create_cvo_az_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP in Azure")

         print_deb("Create new CVO using file: {}".format(args.create_cvo_az_file))
         if (os.path.isfile(args.create_cvo_az_file) != True ):
              print("Error: {} : file not found".format(args.create_cvo_az_file))
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
                   print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
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

         print_deb("Create new CVO using file: {}".format(args.create_cvo_az_ha_file))
         if (os.path.isfile(args.create_cvo_az_ha_file) != True ):
              print("Error: {} : file not found".format(args.create_cvo_az_ha_file))
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
                   print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

    # Arg --cvo-aws-create: Create a new Cloud Volumes ONTAP in AWS
    if args.create_cvo_aws_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP in AWS")

         print_deb("Create new CVO using file: {}".format(args.create_cvo_aws_file))
         if (os.path.isfile(args.create_cvo_aws_file) != True ):
              print("Error: {} : file not found".format(args.create_cvo_aws_file))
              exit(1)
         f = open(args.create_cvo_aws_file)
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
                   print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)


    # Arg --cvo-aws-create-ha: Create a new Cloud Volumes ONTAP HA in AWS
    if args.create_cvo_aws_ha_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP HA in AWS")

         print_deb("Create new CVO using file: {}".format(args.create_cvo_aws_ha_file))
         if (os.path.isfile(args.create_cvo_aws_ha_file) != True ):
              print("Error: {} : file not found".format(args.create_cvo_aws_ha_file))
              exit(1)
         f = open(args.create_cvo_aws_ha_file)
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
                   print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

    # Arg --cvo-gcp-create: Create a new Cloud Volumes ONTAP in GCP
    if args.create_cvo_gcp_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP in GCP")

         print_deb("Create new CVO using file: {}".format(args.create_cvo_gcp_file))
         if (os.path.isfile(args.create_cvo_gcp_file) != True ):
              print("Error: {} : file not found".format(args.create_cvo_gcp_file))
              exit(1)
         f = open(args.create_cvo_gcp_file)
         new_cvo_json=json.load(f)
         print_deb(new_cvo_json)
         f.close

         isHA = False
         cvo_info=netapp_api_cloud.cvo_gcp_create_new(API_TOKEN, account_id, agent_id, isHA, new_cvo_json)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              if (args.json):
                   print(json.dumps(cvo, indent=4))
              else:
                   print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)


    # Arg --cvo-gcp-create-ha: Create a new Cloud Volumes ONTAP HA in GCP
    if args.create_cvo_gcp_ha_file:

         if ( account_id == "" ):
              print("ERROR: miss argument --account-id or current-account-id not set in configuration file")
              exit(1)

         if ( agent_id == "" ):
              print("Error: miss argument --agent-id or current-agent-id not set in configuration file")
              exit(1)

         print("Creates a new Cloud Volumes ONTAP HA in GCP")

         print_deb("Create new CVO using file: {}".format(args.create_cvo_gcp_ha_file))
         if (os.path.isfile(args.create_cvo_gcp_ha_file) != True ):
              print("Error: {} : file not found".format(args.create_cvo_gcp_ha_file))
              exit(1)
         f = open(args.create_cvo_gcp_ha_file)
         new_cvo_json=json.load(f)
         print_deb(new_cvo_json)
         f.close

         isHA = True
         cvo_info=netapp_api_cloud.cvo_gcp_create_new(API_TOKEN, account_id, agent_id, isHA, new_cvo_json)
         print_deb(cvo_info)
         if (cvo_info["status"] == "success"):
              cvo=json.loads(cvo_info["cvo"])
              if (args.json):
                   print(json.dumps(cvo, indent=4))
              else:
                   print("Name:[{}] id:[{}] HA:[{}] svm:[{}] provider:[{}]".format(cvo["name"],cvo["publicId"],cvo["isHA"],cvo["svmName"],cvo["cloudProviderName"]))
         else:
              print("ERROR: {}".format(cvo_info["message"]))
              exit(1)

    # Arg --check-token: Check if API token is still valid
    if args.check_token:
         # Get Token and cloud manager account informations
         print_deb("API Configuration File: {}".format(API_CONFIG_FILE))
         token_info=netapp_api_cloud.check_current_token(API_CONFIG_FILE)
         if ( token_info["status"] == "unknown" ):
              print("ERROR: {}".format(token_info["message"]))
              exit(1)
         print("Access Token is valid")
         exit(0)

    # Arg --version: Check if API token is still valid
    if args.version:
         print("Version {}".format(RELEASE))
         print("API Version {}".format(netapp_api_cloud.API_RELEASE))

except KeyboardInterrupt:
    print ("exit")
    exit(0)
