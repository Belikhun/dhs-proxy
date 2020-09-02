#? |-----------------------------------------------------------------------------------------------|
#? |  proxy.py                                                                                     |
#? |                                                                                               |
#? |  Copyright (c) 2020 Belikhun. All right reserved                                              |
#? |  Licensed under the MIT License. See LICENSE in the project root for license information.     |
#? |-----------------------------------------------------------------------------------------------|

import lib.ehook
from lib.log import log

#> Main Import
import sys
log("OKAY", "Imported: sys")

import re
log("OKAY", "Imported: re")

import os
log("OKAY", "Imported: os")

import zlib
log("OKAY", "Imported: zlib")

import json
log("OKAY", "Imported: json")

import time
log("OKAY", "Imported: time")

import pycurl
log("OKAY", "Imported: pycurl")

from io import BytesIO
log("OKAY", "Imported: io.BytesIO")

import asyncio
log("OKAY", "Imported: asyncio")

import psutil
log("OKAY", "Imported: psutil")

from urllib.parse import urlencode
log("OKAY", "Imported: urllib.parse.urlencode")

import websockets
log("OKAY", "Imported: websockets")

from http.server import BaseHTTPRequestHandler, HTTPServer
log("OKAY", "Imported: http.server")

from socketserver import ThreadingMixIn
log("OKAY", "Imported: socketserver.ThreadingMixIn")

#>

DEBUG = False

if ("--debug" in sys.argv):
	DEBUG = True
	log("DEBG", "Debug Mode Enabled")

if (sys.platform not in ["linux", "linux2", "darwin"]):
	log("ERRR", f"Hệ điều hành hiện tại ({sys.platform}) không được hỗ trợ! Đang thoát...")
	exit(-1)

TIMEOUT = 5

#> Get Wifi and SIM interfaces

WIFIADDR = False
WIFIIFACE = False

DATAADDR = False
DATAIFACE = False
DATAIP = None

ifLists = psutil.net_if_addrs()

for interface in ifLists:
	for addr in ifLists[interface]:
		if (re.match(r"^\d+\.\d+\.\d+\.\d+$", addr.address)):
			if (not WIFIIFACE and ("wlan" in interface or "wifi" in interface)):
				WIFIADDR = addr.address
				WIFIIFACE = interface
				log("OKAY", f"Đã tìm thấy Wifi Interface: {interface} ({WIFIADDR})")

			elif (not DATAIFACE and ("rmnet_data" in interface)):
				DATAADDR = addr.address
				DATAIFACE = interface
				log("OKAY", f"Đã tìm thấy Data Interface: {interface} ({DATAADDR})")

if (DEBUG):
	log("DEBG", f"Merge: {WIFIIFACE} -> dataInterface")
	DATAADDR = WIFIADDR
	DATAIFACE = WIFIIFACE

if (not WIFIADDR):
	log("ERRR", f"Không tìm thấy Wifi Interface! Đang thoát...")
	exit(-1)

if ((not DATAADDR or not DATAIFACE) and not DEBUG):
	log("ERRR", f"Không tìm thấy Data Interface! Đang thoát...")
	exit(-1)

if (not os.path.exists("cookies/")):
	log("WARN", "Cookies Directory Does Not Exist! Creating One")
	os.mkdir("cookies/")

#> Start Web Server

PORT = 25685
COUNT = 0

def getIP():
	log("INFO", f"Getting \"{DATAIFACE}\" IP Address")

	resIO = BytesIO()

	curl = pycurl.Curl()
	curl.setopt(pycurl.URL, "http://httpbin.org/ip")
	curl.setopt(pycurl.INTERFACE, DATAIFACE)
	curl.setopt(pycurl.TIMEOUT, 5)

	curl.setopt(pycurl.WRITEDATA, resIO)

	try:
		# Send Request
		curl.perform()
		data = json.loads(resIO.getvalue().decode("UTF-8"))

		if ("origin" not in data):
			log("ERRR", f"getIP(): Không Tìm Thấy Địa Chỉ IP")
			return;

		log("OKAY", f"Địa Chỉ IP: {data['origin']}")
		return data["origin"]
		
	except (pycurl.error, json.JSONDecodeError) as e:
		log("EXCP", f"getIP(): {e.__doc__}: " + str(e))
		return None

class RequestHandler(BaseHTTPRequestHandler):
	#* =========== OVERWRITE ===========
	def do_GET(self):
		self.requestAt = time.time()

		{
			"/heartbeat": self.SendHeartbeat
		}.get(self.path, lambda: self.response(-1, f"Route Not Found: {self.path}", 404, { "path": self.path }))()

	def do_POST(self):
		self.requestAt = time.time()

		{
			"/request": self.SendRequest,
			"/cookie": self.GetCookie
		}.get(self.path, lambda: self.response(-1, f"Route Not Found: {self.path}", 404, { "path": self.path }))()

	def log_error(self, format, status, message):
		log("ERRR", f"{self.address_string()}: {self.command} {self.path} ({self.request_version}) {status}: {message}")

	def log_message(self, format, command, status, flag = ""):
		log("INFO", f"{self.address_string()}: {self.command} {self.path} ({self.request_version}) {status} {flag}")

	#* =========== ROUTE ===========
	def SendHeartbeat(self):
		self.response(0, "Thành Công!", 200, {
			"cpu": psutil.cpu_percent(),
			"ram": psutil.virtual_memory().percent,
			"ip": DATAIP,
			"interface": DATAIFACE,
			"count": COUNT
		})

	def SendRequest(self):
		global COUNT
		self.requestAt = time.time()

		log("INFO", f"{self.address_string()}: Starting Request")
		COUNT += 1

		if (not self.headers["Content-Length"]):
			COUNT -= 1

			self.response(-1, "'Content-Length' header not set!", 400)
			return

		postData = self.rfile.read(int(self.headers["Content-Length"]))
		jsonData = False

		try:
			jsonData = json.loads(postData)
		except json.JSONDecodeError:
			log("ERRR", f"{self.address_string()}: Malformed POST Data")
			COUNT -= 1

			self.response(-1, "POST Data is not a valid JSON!", 400)
			return

		#> POST DATA CHECK
		if ("url" not in jsonData):
			log("ERRR", f"{self.address_string()}: Chưa Xác Định URL")
			COUNT -= 1

			self.response(-1, "Chưa Xác Định URL", 400)
			return

		url = jsonData["url"]

		if ("method" not in jsonData):
			log("ERRR", f"{self.address_string()}: Chưa Xác Định Method")
			COUNT -= 1

			self.response(-1, "Chưa Xác Định Method", 400)
			return

		method = jsonData["method"].upper()

		if ("jar" not in jsonData):
			log("ERRR", f"{self.address_string()}: Chưa Xác Định CookieJar ID")
			COUNT -= 1

			self.response(-1, "Chưa Xác Định CookieJar ID", 400)
			return

		jarID = jsonData["jar"]

		if (method not in ["GET", "POST", "PUT", "DELETE"]):
			log("ERRR", f"{self.address_string()}: Unsupported Request Method: {method}")
			COUNT -= 1

			self.response(-1, f"Unsupported Request Method: {method}", 400)
			return

		query = jsonData["query"] if ("query" in jsonData) else {}
		form = jsonData["form"] if ("form" in jsonData) else {}
		headers = []

		for key in self.headers:
			if (key.lower() not in ["content-length", "host", "content-type", "origin"]):
				headers.append(f"{key}: {self.headers[key]}")

		if ("type" in jsonData):
			if (jsonData["type"] == "data"):
				headers.append(f"Content-Type: multipart/form-data")
			elif (jsonData["type"] == "json"):
				headers.append(f"Content-Type: application/json")
			else:
				log("ERRR", f"{self.address_string()}: Invalid data type: {jsonData['type']}")
				COUNT -= 1

				self.response(-1, f"Invalid data type: {jsonData['type']}", 400)
				return
		else:
			jsonData["type"] = "json"

		if ("redirect" not in jsonData):
			jsonData["redirect"] = 0

		resIO = BytesIO()
		headIO = BytesIO()

		if (query):
			url += "?"

			for key in query:
				url += f"{key}={query[key]}&"

			url = url[:-1]

		log("DEBG", f"{self.address_string()}: URL: {url}")

		curl = pycurl.Curl()
		curl.setopt(pycurl.URL, url)
		curl.setopt(pycurl.INTERFACE, DATAIFACE)
		curl.setopt(pycurl.HTTPHEADER, headers)
		curl.setopt(pycurl.CUSTOMREQUEST, method)
		curl.setopt(pycurl.FOLLOWLOCATION, not int(jsonData["redirect"]))
		curl.setopt(pycurl.TIMEOUT, 20)

		if (method != "GET"):
			curl.setopt(pycurl.POSTFIELDS, urlencode(form) if (jsonData["type"] == "data") else json.dumps(form))

		log("DEBG", f"{self.address_string()}: Init IO")
		curl.setopt(pycurl.WRITEDATA, resIO)
		curl.setopt(pycurl.WRITEHEADER, headIO)

		log("DEBG", f"{self.address_string()}: Init CookieJar")
		cookieFile = f"cookies/{jarID}.jar"
		curl.setopt(pycurl.COOKIEJAR, cookieFile)

		if (os.path.isfile(cookieFile)):
			curl.setopt(pycurl.COOKIEFILE, cookieFile)
		else:
			log("WARN", f"Cookie Jar ID '{jarID}' does not exist!")
			open(cookieFile, "x")

		curl.setopt(pycurl.SSL_VERIFYPEER, False)
		curl.setopt(pycurl.SSL_VERIFYHOST, False)

		try:
			# Send Request
			curl.perform()
			log("DEBG", f"{self.address_string()}: Request Performed")
		except pycurl.error as e:
			log("EXCP", f"{self.address_string()}: {e.__doc__}: " + str(e))
			COUNT -= 1

			self.response(-1, f"{e.__doc__}: {str(e)}", 500)
			return

		statusCode = curl.getinfo(pycurl.HTTP_CODE)
		headersData = headIO.getvalue().decode("UTF-8").splitlines()
		responseData = resIO.getvalue()

		try:
			responseData = responseData.decode("UTF-8")
		except UnicodeDecodeError:
			responseData = zlib.decompress(responseData, 15 + 32).decode("UTF-8")
		
		responseHeaders = {}

		for line in headersData:
			if (": " not in line):
				continue

			key, value = line.split(": ")
			responseHeaders[key] = value

		try:
			responseData = json.loads(responseData)
		except ValueError:
			pass

		COUNT -= 1
		self.response(0, f"Request completed with status {statusCode}", statusCode, responseData, responseHeaders)

		log("OKAY", f"{self.address_string()}: Request Hoàn Thành ({statusCode})")

	def GetCookie(self):
		if (not self.headers["Content-Length"]):
			self.response(-1, "'Content-Length' header not set!", 400)
			return

		postData = self.rfile.read(int(self.headers["Content-Length"]))
		jsonData = False

		try:
			jsonData = json.loads(postData)
		except json.JSONDecodeError:
			log("ERRR", f"{self.address_string()}: Malformed POST Data")
			self.response(-1, "POST Data is not a valid JSON!", 400)
			return

		if ("jar" not in jsonData):
			log("ERRR", f"{self.address_string()}: Chưa Xác Định CookieJar ID")
			self.response(-1, "Chưa Xác Định CookieJar ID", 400)
			return

		jarID = jsonData["jar"]
		
		if ("url" not in jsonData):
			log("ERRR", f"{self.address_string()}: Chưa Xác Định URL")
			self.response(-1, "Chưa Xác Định URL", 400)
			return

		url = jsonData["url"]

		if ("name" not in jsonData):
			log("ERRR", f"{self.address_string()}: Chưa Xác Định Cookie Name")
			self.response(-1, "Chưa Xác Định Cookie Name", 400)
			return

		name = jsonData["name"]

		cookieFile = f"cookies/{jarID}.jar"
		if (not os.path.isfile(cookieFile)):
			log("WARN", f"Cookie Jar ID '{jarID}' does not exist!")
			self.response(-1, f"Cookie Jar ID '{jarID}' does not exist!", 400)

		matches = []

		with open(cookieFile, mode = "r") as file:
			lines = file.readlines()

			for line in lines:
				if (line[0] == "#"):
					continue

				match = re.match(r"^(.+)\s+(.+)\s+(.+)\s+(.+)\s+(\d+)\s+(.+)\s+(.+)$", line)

				if (not match):
					continue

				if ((url not in (match.group(1) + match.group(3))) or (match.group(6) != name)):
					continue

				matches.append({
					"domain": match.group(1),
					"subdomain": (match.group(2) == "TRUE"),
					"path": match.group(3),
					"https": (match.group(4) == "TRUE"),
					"expires": int(match.group(5)),
					"name": match.group(6),
					"value": match.group(7)
				})

			self.response(0, f"Success!", 200, matches)


	#* =========== OTHER ===========
	def response(self, code, description, status, data = None, headers = {}):
		"""
		Main function for sending back response data followed by my API design
		"""

		self.send_response(status if (status != 204) else 200)
		self.send_header("Content-Type", "application/json;charset=UTF-8")
		self.send_header("Status", status)

		for header in headers:
			if (header.lower() not in ("date", "server", "content-type", "content-length", "content-encoding", "status", "connection", "set-cookie", "location")):
				self.send_header(header, headers[header])

		resData = bytes(json.dumps({
			"code": code,
			"description": description,
			"status": status,
			"headers": headers,
			"data": data,
			"runtime": time.time() - self.requestAt
		}), "utf-8")

		self.send_header("Content-Length", len(resData))
		self.end_headers()
		self.wfile.write(resData)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass

if __name__ == "__main__":

	DATAIP = getIP()

	webServer = ThreadedHTTPServer((WIFIADDR, PORT), RequestHandler)
	log("OKAY", f"Máy chủ đang chạy tại {WIFIADDR}:{PORT}")

	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	log("OKAY", f"Máy chủ đã đóng")