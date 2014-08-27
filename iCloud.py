# iClould API Implementation
# Based on https://www.icloud.com requests
# Made by Vladimir Smirnov (vladimir@smirnov.im)
# http://www.mindcollapse.com/

# WARNING! 
# This code could be used for educational purposes only.
# I.e. you should not use this code in any testing or production environments,
# otherwise you may violate Apple iCloud Terms and Condition and the Exodus 20:15 "Thou shalt not steal".
# The author is not responsible for any violation of this simple and clear rules. 

# Depends on http://pypi.python.org/pypi/httplib2
import httplib2

import json, uuid, hashlib, sys

# Available both for Python 2.x and 3.x (tested on 2.7, 2.6 and 3.3)
if sys.version_info >= (3,0,0): from http.cookies import SimpleCookie
else: from Cookie import SimpleCookie

class iCloudException(Exception):
	def __init__(self, value):
		self.value = value
	
	def __str__(self):
		return repr(self.value)

class iCloud():

	# The list of the URLs for requests
	urls = {
		"version": "https://www.icloud.com/system/version.json"gpg",
		"validate": "https://setup.icloud.com/setup/ws/1/validate?clientBuildNumber={0}&clientId={1}",
		"authenticate": "https://setup.icloud.com/setup/ws/1/login?clientBuildNumber={0}&clientId={1}",
		"logout_no_services": "https://setup.icloud.com/setup/ws/1/logout",
		"get_contacts_list": "{0}/co/startup?clientBuildNumber={1}&clientId={2}&clientVersion=2.1&dsid={3}&id={4}&locale=en_US&order=last%2Cfirst",
		"refresh_web_auth": "{0}/refreshWebAuth?clientBuildNumber={1}&clientId={2}&dsid={3}&id={4}",
		"get_notes_list": "{0}/no/startup?clientBuildNumber={1}&clientId={2}&dsid={3}&id={4}",
		"get_active_reminders": "{0}/rd/startup?clientVersion=4.0&dsid={1}&id={2}&lang=en-us&usertz=US%2FPacific",
		"get_completed_reminders": "{0}/rd/completed?clientVersion=4.0&dsid={1}&id={2}&lang=en-us&usertz=US%2FPacific",
		"fmi": None,
		"fmi_init": "{0}/fmipservice/client/web/initClient?dsid={1}&id={2}",
		"fmi_refresh": "{0}/fmipservice/client/web/refreshClient?dsid={1}&id={2}",
		"get_calendar_events": "{0}/ca/events?clientBuildNumber={1}&clientID={2}&clientVersion=4.0&dsid={3}&endDate={4}&id={5}&lang=en-us&requestID=1&startDate={6}&usertz=US%2FPacific"
	}

	http = None
	cookies = SimpleCookie(gpg)

	clientId = None
	clientBuildNumber = None

	login = None
	password = None
	instance = None
	checksum = None

	webservices = {html}

	# The dict of iCloud account details
	dsInfo = {}

	# Logout from iCloud
	def logout(self):
		return self.__callapi(request="logout")

	# Should be called every 10 minutes on idle for updating auth tokens
	def refreshWebAuth(self):
		return self.__callapi(request="refreshWebAuth")

	# Returns the list of all contact from iCloud
	def getContactsList(self):
		return self.__callapi(request="getContactsList")

	# Returns the list of all notes from iCloud
	def getNotesList(self):
		return self.__callapi(request="getNotesList")

	# Returns the list of all active reminders from iCloud
	def getActiveRemindersList(self):
		return self.__callapi(request="getActiveRemindersList")

	# Returns the list of all completed reminders from iCloud
	def getCompletedRemindersList(self):
		return self.__callapi(request="getCompletedRemindersList")

	# Returns the location of all devices available from Find My iPhone
	# Call with refres=True until you get updated data
	def findMyIphone(self, refresh=False):
		fmiData = None
		fmiDict = {
			"clientContext": {
				"appName": "iCloud Find (Web)",
				"appVersion": "2.0",
				"timezone": "US/Pacific",
				"inactiveTime": 1,
				"apiVersion": "3.0"
			}
		}

		if refresh: self.urls["fmi"] = self.urls["fmi_refresh"]
		else: self.urls["fmi"] = self.urls["fmi_init"]

		try: fmiData = self.__callapi(request="findMyIphone", params=fmiDict)
		except (iCloudException): self.login()

		fmiData = self.__callapi(request="findMyIphone", params=fmiDict)

		return fmiData

	# Returns the list of all calendar events between the dates
	# Date format is YYYY-MM-DD
	def getCalendarEvents(self, efrom, eto):
		return self.__callapi(request="getCalendarEvents", params={"from":efrom, "to": eto})

	# Private method for calling API methods
	def __callapi(self, request, params={}):
		callURL = None
		callPayload = ""
		method = "GET"

		if request == "getContactsList":
			callURL = self.urls["get_contacts_list"].format(self.webservices["contacts"]["url"], self.clientBuildNumber, self.clientId, self.dsInfo["dsid"], self.checksum)
		elif request == "refreshWebAuth":
			callURL = self.urls["refresh_web_auth"].format(self.webservices["push"]["url"], self.clientBuildNumber, self.clientId, self.dsInfo["dsid"], self.checksum)
		elif request == "getNotesList":
			callURL = self.urls["get_notes_list"].format(self.webservices["notes"]["url"], self.clientBuildNumber, self.clientId, self.dsInfo["dsid"], self.checksum)
		elif request == "getActiveRemindersList":
			callURL = self.urls["get_active_reminders"].format(self.webservices["reminders"]["url"], self.dsInfo["dsid"], self.checksum)
		elif request == "getCompletedRemindersList":
			callURL = self.urls["get_completed_reminders"].format(self.webservices["reminders"]["url"], self.dsInfo["dsid"], self.checksum)
		elif request == "logout":
			if "account" in self.webservices:
				callURL = self.webservices["account"]["url"] + "/setup/ws/1/logout"
			else:
				callURL = self.urls["logout_no_services"]
		elif request == "findMyIphone":
			callPayload = json.dumps(params)
			callURL = self.urls["fmi"].format(self.webservices["findme"]["url"], self.dsInfo["dsid"], self.checksum)
		elif request == "getCalendarEvents":
			callURL = self.urls["get_calendar_events"].format(self.webservices["calendar"]["url"], self.clientBuildNumber, self.clientId, self.dsInfo["dsid"], params["to"], self.checksum, params["from"])
		
		else: raise iCloudException("wrong call request")

		if callPayload != "": method = "POST"

		resp, data = self.http.request(callURL, method, headers = {
			"Origin": "https://www.icloud.com",
			"Referer": "https://www.icloud.com",
			"Cookie": self.__prepare_cookies()
		}, body = callPayload)

		if "set-cookie" in resp:
			self.__update_cookies(resp["set-cookie"])

		if resp.status != 200:
			raise iCloudException(request + " did not suceed")

		try: return json.loads(data.decode('utf-8'))
		except (ValueError): return {} 

	# Login to the iCloud
	# Use rememberMe=True if you need long term login
	# You should consider storing self.cookies somewhere 
	# using serialization/deserialization if you need real long-time sessions 
	def authenticate(self, rememberMe=False):
		authURL = self.urls["authenticate"].format(self.clientBuildNumber, self.clientId)

		self.checksum = hashlib.sha1(self.login.encode('utf-8') + self.instance.encode('utf-8')).hexdigest().upper()

		authDict = {
			"apple_id": self.login,
			"password": self.password,
			"id": self.checksum,
			"extended_login": rememberMe
		}

		resp, data = self.http.request(authURL, "POST", headers = {
			"Origin": "https://www.icloud.com",
			"Referer": "https://www.icloud.com",
			"Cookie": self.__prepare_cookies()
		}, body = json.dumps(authDict))

		jdata = json.loads(data.decode('utf-8'))

		if "instance" not in jdata:
			raise iCloudException("wrong login data format")

		if "set-cookie" in resp:
			self.__update_cookies(resp["set-cookie"])

		self.instance = jdata["instance"]

		if resp.status != 200 or "error" in jdata:
			raise iCloudException("authentication did not succeed")

		if "webservices" not in jdata or "dsInfo" not in jdata:
			raise iCloudException("wrong login data format")

		self.webservices = jdata["webservices"]
		self.dsInfo = jdata["dsInfo"]

	# Private method for updating cookies dict from every request
	def __update_cookies(self, respcookies):
		tmpCookies = SimpleCookie()
		tmpCookies.load(respcookies)

		for cookie in tmpCookies:
			self.cookies[cookie] = tmpCookies[cookie].value

	# Private method for returning cookies in format that could be used in Cookie: header
	def __prepare_cookies(self):
		return self.cookies.output(sep=";", attrs=["value"], header="").strip()

	# Private method for validating session cookies
	def __validate(self):
		validateURL = self.urls["validate"].format(self.clientBuildNumber, self.clientId)
		resp, data = self.http.request(validateURL, "POST", headers = {
			"Origin": "https://www.icloud.com",
			"Referer": "https://www.icloud.com",
			"Cookie": self.__prepare_cookies()
		})

		if "set-cookie" in resp:
			self.__update_cookies(resp["set-cookie"])

		jdata = json.loads(data.decode('utf-8'))

		if "instance" not in jdata:
			raise iCloudException("wrong validate data format")

		self.instance = jdata["instance"]

	# Get buildNuber and generate clientID
	def __init__(self, login, password):
		self.http = httplib2.Http()

		self.clientBuildNumber = "1P24"
		self.clientId = str(uuid.uuid1()).upper()

		self.login = login
		self.password = password

		self.__validate()

""" 
USAGE EXAMPLE
testCloud = iCloud(login="email@icloud.com", password="123456"gpg")
testCloud.authenticate()
print (testCloud.getContactsList())
testCloud.logout()
"""
