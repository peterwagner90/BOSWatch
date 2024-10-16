#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Divera-Plugin to send FMS-, ZVEI- and POCSAG - messages to Divera
@author: Marco Grosjohann
@requires: Divera-Configuration has to be set in the config.ini
"""

import json
import logging  # Global logger
import http.client  # for the HTTP request
import re
import urllib.request, urllib.parse, urllib.error
from includes import globalVars  # Global variables

# from includes.helper import timeHandler
from includes.helper import configHandler
from includes.helper import wildcardHandler

def isSignal(poc_id):
	"""
	@type    poc_id: string
	@param   poc_id: POCSAG Ric

	@requires:  Configuration has to be set in the config.ini

	@return:    True if the Ric is Signal, other False
	@exception: none
	"""
	# If RIC is Signal return True, else False
	if globalVars.config.get("POC", "netIdent_ric"):
		if poc_id in globalVars.config.get("POC", "netIdent_ric"):
			logging.info("RIC %s is net ident", poc_id)
			return True
		else:
			logging.info("RIC %s is no net ident", poc_id)
			return False

##
#
# onLoad (init) function of plugin
# will be called one time by the pluginLoader on start
#
def onLoad():
    """
    While loading the plugins by pluginLoader.loadPlugins()
    this onLoad() routine is called one time for initialize the plugin
    @requires:  nothing
    @return:    nothing
    """
    # nothing to do for this plugin
    return


##
#
# Main function of Divera-plugin
# will be called by the alarmHandler
#
def run(typ, freq, data):
    """
    This function is the implementation of the Divera-Plugin.
    It will send the data to Divera API
    @type    typ:  string (FMS|ZVEI|POC)
    @param   typ:  Typ of the dataset
    @type    data: map of data (structure see readme.md in plugin folder)
    @param   data: Contains the parameter
    @type    freq: string
    @keyword freq: frequency of the SDR Stick
    @requires:  Divera-Configuration has to be set in the config.ini
    @return:    nothing
    """
    try:
        if configHandler.checkConfig("Divera"):  # read and debug the config

            if typ == "FMS":
                #
                # building message for FMS
                #
                text = globalVars.config.get("Divera", "fms_text")
                title = globalVars.config.get("Divera", "fms_title")
                priority = globalVars.config.get("Divera", "fms_prio")
                vehicle = globalVars.config.get("Divera", "fms_vehicle")

            elif typ == "ZVEI":
                #
                # building message for ZVEI
                #
                text = globalVars.config.get("Divera", "zvei_text")
                title = globalVars.config.get("Divera", "zvei_title")
                priority = globalVars.config.get("Divera","zvei_prio")
                zvei_id = globalVars.config.get("Divera","zvei_id")

            elif typ == "POC":
                if isSignal(data["ric"]): 
                
                    logging.debug("RIC is net ident")
                    return
                else:
                    #
                    # building message for POC
                    #
                    if data["function"] == '1':
                        priority = globalVars.config.get("Divera", "SubA")
                    elif data["function"] == '2':
                        priority = globalVars.config.get("Divera", "SubB")
                    elif data["function"] == '3':
                        priority = globalVars.config.get("Divera", "SubC")
                    elif data["function"] == '4':
                        priority = globalVars.config.get("Divera", "SubD")
                    else:
                        priority = ''
                        
                    text = globalVars.config.get("Divera", "poc_text")
                    title = globalVars.config.get("Divera", "poc_title")
                    ric = globalVars.config.get("Divera", "poc_ric")
                    

            else:
                logging.warning("Invalid type: %s", typ)
                return

        try:
            #
            # Divera-Request
            #
            logging.debug("send Divera for %s", typ)
            
            # Replace wildcards & Logging data to send
            title = wildcardHandler.replaceWildcards(title, data)
            logging.debug("Title   : %s", title)
            text = wildcardHandler.replaceWildcards(text, data)
            logging.debug("Text    : %s", text)
            
            # Remove AxxSRS and (11:11) from title
            title = re.sub(r'^\s*A\d+SRS\s*\(\d{2}:\d{2}\)\s*', '', title)
            if typ == "FMS":
                vehicle = wildcardHandler.replaceWildcards(vehicle, data)
                logging.debug("Vehicle     : %s", vehicle)
            elif typ == "POC":
                ric = wildcardHandler.replaceWildcards(ric, data)
                logging.debug("RIC     : %s", ric)
            elif typ == "ZVEI":
                zvei_id = wildcardHandler.replaceWildcards(zvei_id, data)
                logging.debug("ZVEI_ID     : %s", zvei_id)
            else:
                logging.info("No wildcards to replace and no Typ selected!")
				
            # check priority value
            if (priority != 'false') and (priority != 'true'):
                logging.info("No Priority set for type '%s'! Skipping Divera-Alarm!", typ)
                return

            # Check FMS
            if typ == "FMS":
                if (vehicle == ''):
                    logging.info("No Vehicle set!")
            
            # Check POC
            elif typ == "POC":
                if (ric == ''):
                    logging.info("No RIC set!")
             
            # Check ZVEI       
            elif typ == "ZVEI":
                if (zvei_id == ''):
                    logging.info("No ZVEI_ID set!")
                    
            else:
                logging.info("No ZVEI, FMS or POC alarm")
            
            # start connection to Divera
            conn = http.client.HTTPSConnection("www.divera247.com:443")
            conn2 = http.client.HTTPSConnection("www.divera247.com:443")
            conn3 = http.client.HTTPSConnection("www.divera247.com:443")                
            if typ == "FMS":
                # start the connection FMS
                conn.request("GET", "/api/fms",
                             urllib.parse.urlencode({
                                "accesskey": globalVars.config.get("Divera", "accesskey"),
                                "vehicle_ric": vehicle,
                                "status_id": data["status"],
                                "status_note": data["directionText"],
                                "title": title,
                                "text": text,
                                "priority": priority,
                            }))
                            
            elif typ == "ZVEI":
            # start connection ZVEI; zvei_id in Divera is alarm-RIC!
                conn.request("GET", "/api/alarm",
                            urllib.parse.urlencode({
                                "accesskey": globalVars.config.get("Divera", "accesskey"),
                                "title": title,
                                "ric": zvei_id,
                                "text": text,
                                "priority": priority,
                            }))
            
            elif typ == "POC":
            # start connection POC  
                if (ric == ''):
                    conn.request("GET", "/api/alarm",
                                urllib.parse.urlencode({
                                    "accesskey": globalVars.config.get("Divera", "accesskey"),
                                    "title": title,
                                    "text": text,
                                    "priority": priority,
                                }))
                else:
                    conn.request("GET", "/api/alarm",
                                urllib.parse.urlencode({
                                    "accesskey": globalVars.config.get("Divera", "accesskey"),
                                    "title": title,
                                    "ric": ric,
                                    "text": text,
                                    "priority": priority,
                                }))
                                      
            
            else:
                logging.debug("No Type is set", exc_info=True)
                return

        except:
            logging.error("cannot send Divera request")
            logging.debug("cannot send Divera request", exc_info=True)
            return

        try:
            #
            # check Divera-Response
            #
            response = conn.getresponse()
            if str(response.status) == "200":  # Check Divera Response and print a Log or Error
                logging.debug("Divera response: %s - %s", str(response.status), str(response.reason))
            else:
                logging.warning("Divera response: %s - %s", str(response.status), str(response.reason))
            response.read() # read the response to clear the buffer

            if str(response.status) == "200":        
                # Make a GET request to /api/last-alarm using the accesskey
                conn2.request("GET", "/api/last-alarm",
                        urllib.parse.urlencode({
                        "accesskey": globalVars.config.get("Divera", "accesskey")
                        }))
                
                # Check the response status
                response = conn2.getresponse()
                if str(response.status) == "200":
                    # Response is 200, do something with the response data
                    data = response.read()
                    json_data = data.decode('utf-8')
                    message_channel_id = json.loads(json_data)['message_channel_id']
                    # Process the response data here
                    # Construct the JSON payload
                    payload = {
                        "Message": {
                            "message_channel_id": message_channel_id,
                            "parent_id": 0,
                            "text": text,
                            "uploads": "Binary"
                        }
                    }

                    # Convert the payload to JSON string
                    payload_json = json.dumps(payload)

                    # Make a POST request to the REST API
                    conn3.request("POST", "/api/v2/messages",
                                urllib.parse.urlencode({
                                "accesskey": globalVars.config.get("Divera", "messageaccesskey")
                                }),
                                body=payload_json,
                                headers={"Content-Type": "application/json"})

                    # Check the response status
                    response = conn3.getresponse()
                    if str(response.status) == "200":
                        # Response is 200, do something with the response data
                        data = response.read()
                    else:
                        # Response is not 200, handle the error
                        logging.warning("Divera  response: %s - %s", str(response.status), str(response.reason))
                else:
                    # Response is not 200, handle the error
                    logging.warning("Divera  response: %s - %s", str(response.status), str(response.reason))
            else:
                # Response is not 200, handle the error
                logging.warning("Divera response: %s - %s", str(response.status), str(response.reason))
        except:  # otherwise
            logging.error("cannot get Divera response")
            logging.debug("cannot get Divera response", exc_info=True)
            return

        finally:
            logging.debug("close Divera-Connection")
            try:
                conn.close()
                conn2.close()
                conn3.close()
            except:
                pass
        
    except:
        logging.error("unknown error")
        logging.debug("unknown error", exc_info=True)
