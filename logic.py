# Copyright (c) 2008, Media Modifications Ltd.

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.


from result import ServerResult
from constants import Constants
from instance import Instance

from threading import Thread
import threading
import os
import gobject
import time
import gtk
import urllib

class ServerLogic:
	def __init__(self, ca):
		self.ca = ca
		self.proceedTxt = ""
		self.proceedHeaders = []
		self.cond = ca.cond
		self.addKMLSet=0

	def doServerLogic(self, url, path, params):
		self.ca.remoteServerActive( True )
		r = ServerResult()
		fileName = path[len(path)-1]

		if (fileName == "comet.js"):

			#clear...
			self.proceedHeaders = []
			self.proceedTxt = ""

			#wait...
			self.cond.acquire()
			self.cond.wait()
			self.cond.release()

			#prep response...
			for h in range( len(self.proceedHeaders) ):
				r.headers.append( self.proceedHeaders[h] )
			r.txt = ""+self.proceedTxt

		else:
			kickThroughComet = True

			if (fileName =="mediaQuery.js"):
				self.proceedHeaders.append( ("Content-type", "text/javascript") )
				self.proceedTxt = self.ca.m.getMediaResponse( params[0][1], params[1][1], params[2][1], params[3][1] )

			elif (fileName == "showMedia.js"):
				id = params[0][1]
				locX = params[1][1]
				locY = params[2][1]
				up = params[3][1]
				rt = params[4][1]
				gobject.idle_add(self.ca.showMedia, id, locX, locY, up=='true', rt=='true')
				self.proceedHeaders.append( ("Content-type", "text/javascript") )

			elif (fileName == "placeAddMedia.js"):
				lat = params[0][1]
				lng = params[1][1]
				gobject.idle_add(self.ca.placeAddMedia, lat, lng)
				self.proceedHeaders.append( ("Content-type", "text/javascript") )
				kickThroughComet = False

			elif (fileName == "hideMedia.js"):
				gobject.idle_add(self.ca.hideMedia)

			elif (fileName == "getImage.js"):
				localfile = open(os.path.join(Instance.instancePath, params[0][1]), 'r')
				localdata = localfile.read()
				localfile.close()

				#one day we might need to kick you through comet as a base64'd image.
				r.txt = localdata
				r.headers.append( ("Content-type", "image/jpeg") )
				kickThroughComet = False

			elif (fileName == "updateLocation.js"):
				lat = params[0][1]
				lng = params[1][1]
				zoom = params[2][1]
				x = params[3][1]
				y = params[4][1]
				gobject.idle_add(self.ca.updateMapMetaData,lat,lng,zoom,x,y)

			elif (fileName == "addSavedMap.js"):
				# allow internet to send an array of SavedMaps back to map.py
				latitudes = params[0][1]
				longitudes = params[1][1]
				zooms = params[2][1]
				notes = params[3][1]
				gobject.idle_add(self.ca.addSavedMap,latitudes,longitudes,zooms,urllib.unquote(notes),True)

			elif (fileName == "addInfoMarker.js"):
				lat = params[0][1]
				lng = params[1][1]
				info = params[2][1]
				icon = params[3][1]
				if(params[4][1] == "True"):
					isNew = True
				else:
					isNew = False
				gobject.idle_add(self.ca.addInfoMarker,lat,lng,info,icon,isNew)
			
			elif (fileName == "addLine.js"):
				id = params[0][1]
				color = params[1][1]
				thickness = params[2][1]
				pts = params[3][1]  # send pts separated with | instead of ,
				gobject.idle_add(self.ca.addLine,id,color,thickness,pts)
			
			elif (fileName == "promptSearch.js"):
				address = params[0][1]
				time.sleep(0.5)
				self.ca.preComet()
				self.handleAddressUpdate(address+"+")
				self.ca.postComet()

			#elif (fileName == "gotoMapV3.js"):
				# button on static maps links to mapv3
				#self.ca.loadMapV3()

			if (kickThroughComet):
				#not sure how & why this goes out, but it does.
				self.cond.acquire()
				self.cond.notifyAll()
				self.cond.release()
				time.sleep(.1)

		return r

	def handleAddressUpdate( self, address ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "moveToAddress('" + address  + "');"

	def handleCompassUpdate( self, dir ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )

		if (dir == "e"):
			self.proceedTxt = "dirEast();"
		elif (dir == "w"):
			self.proceedTxt = "dirWest();"
		elif (dir == "n"):
			self.proceedTxt = "dirNorth();"
		elif (dir == "s"):
			self.proceedTxt = "dirSouth();"
		else:
			# use this as a print warning window
			self.proceedTxt = 'showInfo("' + dir + '");'

	def handleZoomUpdate( self, dir ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		if (dir == "+"):
			self.proceedTxt = "zoomIn();"
		elif (dir == "-"):
			self.proceedTxt = "zoomOut();"

	def handleClear( self ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "clear();"

	def handlePreAdd( self ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "preAddMedia();"

	def handlePreAddInfo( self ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "preAddInfo();"

	def handlePostAdd( self, rec  ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "postAddMedia(" + rec.latitude + ", " + rec.longitude + ", '" + rec.getThumbUrl() + "', '" + rec.getThumbBasename() + "', '" + rec.tags + "');"

	def handleDelete( self ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "deleteMedia();"

	# handle a map that was sent to us
	def handleReceivedMap( self, lat, lng, zoom):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "setMap(" + lat + "," + lng + "," + zoom + ");"

	def handleSavedMap( self, lat, lng, zoom, info ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		if(info.find("Describe the map") != 0):
			self.proceedTxt = "setMap2(" + lat + "," + lng + "," + zoom + ",'" + urllib.quote(info) + "');"
		else:
			self.proceedTxt = "setMap2(" + lat + "," + lng + "," + zoom + ",'');"			

	# handle a marker that was sent to us
	def handleAddMarker( self, lat, lng, pixString, icon ):
		if(self.addKMLSet == 0):
			self.proceedHeaders.append( ("Content-type", "text/javascript") )
			self.proceedTxt = ""
			self.addKMLSet = 1
		self.proceedTxt = self.proceedTxt + "addInfoMarker(" + lat + ", " + lng + ", '" + pixString + "', '" + icon + "',false);"

	def handleEndKML( self ):
		self.addKMLSet = 0

	def lineMode(self, type):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "lineMode('" + type + "');"

	def handleLine(self,id,color,thickness,pts):
		if(self.addKMLSet == 0):
			self.proceedHeaders.append( ("Content-type", "text/javascript") )
			self.proceedTxt = ""
			self.addKMLSet = 1
		self.proceedTxt = self.proceedTxt + "addLine('" + id + "','" + color + "','" + thickness + "','" + pts + "');"

	# handle start of measure tool
	def handleMeasure(self):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "measure();"

	def handleTagSearch( self, tags ):
		self.proceedHeaders.append( ("Content-type", "text/javascript") )
		self.proceedTxt = "filterTags('" + tags + "');"
