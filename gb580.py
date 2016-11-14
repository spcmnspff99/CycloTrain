from __future__ import with_statement
import os, sys, glob

import math
import time, datetime
import ConfigParser
import logging
import appdirs
from decimal import Decimal

import serial
from serial.tools import list_ports
from pytz import timezone, utc

from templates import Template
from gpxParser import GPXParser
from Utilities import Utilities

class Coordinate(Decimal):     
    def __hex__(self):
        return Utilities.coord2hex(Decimal(self))
    
    def fromHex(self, hex):
        if len(hex) == 8:
            self = Coordinate(Utilities.hex2coord(hex))
            return self
        else:
            raise GB500ParseException(self.__class__.__name__, len(hex), 8)

class Point(object):
    def __init__(self, latitude = 0, longitude = 0):
        self.latitude  = Coordinate(latitude)
        self.longitude = Coordinate(longitude)
        
    def __getitem__(self, attr):
        return getattr(self, attr)
        
    def __hex__(self):
        return '%s%s' % (hex(self.latitude), hex(self.longitude))
    
    def fromHex(self, hex):
        if len(hex) == 16:
            self.latitude = Coordinate().fromHex(hex[:8])
            self.longitude = Coordinate().fromHex(hex[8:])
            return self
        else:
            raise GB500ParseException(self.__class__.__name__, len(hex), 16)


class Trackpoint(Point):    
    def __init__(self, latitude = 0, longitude = 0, altitude = 0, speed = 0, heartrate = 0, cadence = 0, pwrcadence = 0, power = 0, temp = 0, interval = 0, date = datetime.datetime.utcnow()):
        self.altitude    = altitude
        self.speed       = speed
        self.heartrate   = heartrate
        self.interval    = interval
        self.cadence     = cadence
        self.pwrcadence  = pwrcadence
        self.power       = power
        self.temp        = temp
        self.date        = date
        super(Trackpoint, self).__init__(latitude, longitude)
    
    def __getitem__(self, attr):
        return getattr(self, attr)
        
    def __str__(self):
        return "(%f, %f, %i, %i, %i, %i)" % (self.latitude, self.longitude, self.altitude, self.speed, self.heartrate, self.interval, self.cadence, self.power, self.temp)

    def fromHex(self, hex):
        if len(hex) == 64:
            self.latitude   = Coordinate().fromHex(Utilities.swap(hex[0:8]))
            self.longitude  = Coordinate().fromHex(Utilities.swap(hex[8:16]))
            self.altitude   = Utilities.hex2signedDec(Utilities.swap(hex[16:20]))
            self.speed      = int(Utilities.swap(hex[24:32]), 16)/100
            self.heartrate  = int(Utilities.swap(hex[32:34]), 16)
            self.interval   = int(Utilities.swap(hex[40:48]), 16)
            #self.interval   = datetime.timedelta(seconds=Utilities.hex2dec(hex[40:48])/10.0)
            self.cadence    = int(Utilities.swap(hex[48:52]), 16)
            self.pwrcadence = int(Utilities.swap(hex[42:56]), 16)
            self.power      = int(Utilities.swap(hex[56:60]), 16)
            self.temp       = int(Utilities.swap(hex[60:64]), 16)
            return self
        else:
            raise GB500ParseException(self.__class__.__name__, len(hex), 64)
    
    def calculateDate(self, dt):
        self.date = dt + datetime.timedelta(milliseconds = (self.interval * 100))


class Waypoint(Point):
    TYPES = {
        0:  'DOT',
        1:  'HOUSE',
        2:  'TRIANGLE',
        3:  'TUNNEL',
        4:  'CROSS',
        5:  'FISH',
        6:  'LIGHT',
        7:  'CAR',
        8:  'COMM',
        9:  'REDCROSS',
        10: 'TREE',
        11: 'BUS',
        12: 'COPCAR',
        13: 'TREES',
        14: 'RESTAURANT',
        15: 'SEVEN',
        16: 'PARKING',
        17: 'REPAIRS',
        18: 'MAIL',
        19: 'DOLLAR',
        20: 'GOVOFFICE',
        21: 'CHURCH',
        22: 'GROCERY',
        23: 'HEART',
        24: 'BOOK',
        25: 'GAS',
        26: 'GRILL',
        27: 'LOOKOUT',
        28: 'FLAG',
        29: 'PLANE',
        30: 'BIRD',
        31: 'DAWN',
        32: 'RESTROOM',
        33: 'WTF',
        34: 'MANTARAY',
        35: 'INFORMATION',
        36: 'BLANK'
    }
    
    def __init__(self, latitude = 0, longitude = 0, altitude = 0, title = '', type = 0):
        self.altitude = altitude
        self.title = title
        self.type = type
        super(Waypoint, self).__init__(latitude, longitude) 
                
    def __str__(self):
        return "%s (%f,%f)" % (self.title, self.latitude, self.longitude)
        
    def __hex__(self):
        return "%(title)s00%(type)s%(altitude)s0000%(latitude)s%(longitude)s" % {
            'latitude'  : Utilities.swap(hex(self.latitude)),
            'longitude' : Utilities.swap(hex(self.longitude)),
            'altitude'  : Utilities.swap(Utilities.dec2hex(self.altitude,4)),
            'type'      : Utilities.dec2hex(self.type,2),
            'title'     : Utilities.chr2hex(self.title.ljust(6)[:6])
        }
        
    def fromHex(self, hex):
        if len(hex) == 40:            
            def safeConvert(c):
                #if hex == 00 chr() converts it to space, not \x00
                if c == '00':
                    return ' '
                else:
                    return Utilities.hex2chr(c)
                
            self.latitude = Coordinate().fromHex(Utilities.swap(hex[24:32]))
            self.longitude = Coordinate().fromHex(Utilities.swap(hex[32:40]))
            self.altitude = Utilities.hex2signedDec(Utilities.swap(hex[16:20]))
            self.title = safeConvert(hex[0:2])+safeConvert(hex[2:4])+safeConvert(hex[4:6])+safeConvert(hex[6:8])+safeConvert(hex[8:10])+safeConvert(hex[10:12])
            self.type = Utilities.hex2dec(hex[12:16])
            
            return self
        else:
            raise GB500ParseException(self.__class__.__name__, len(hex), 40)


class Lap(object):
    def __init__(self, start = datetime.datetime.now(), end = datetime.datetime.now(), duration = datetime.timedelta(), distance = 0, calories = 0,
                 maxSpeed = 0, maxHeartrate = 0, avgHeartrate = 0, minAltitude = 0, maxAltitude = 0, avgCadence = 0, maxCadence =0, avgPower = 0,
                 maxPower = 0, startPoint = Point(0,0), endPoint = Point(0,0)):
        self.start        = start
        self.end          = end
        self.duration     = duration
        self.distance     = distance
        self.calories     = calories
        self.maxSpeed     = maxSpeed
        self.maxHeartrate = maxHeartrate
        self.avgHeartrate = avgHeartrate
        self.minAltitude  = minAltitude
        self.maxAltitude  = maxAltitude
        self.avgCadence   = avgCadence
        self.maxCadence   = maxCadence
        self.avgPower     = avgPower
        self.maxPower     = maxPower
        self.startPoint   = startPoint
        self.endPoint     = endPoint
        
    def __str__(self):
        return "%s %s %s %08i %06i %04i %04i" % (self.start, self.end, self.duration, self.distance, self.calories,self.avgHeartrate, self.avgCadence)

    def __getitem__(self, attr):
        return getattr(self, attr)

    def fromHex(self, hex):
        if len(hex) == 96:
            self.__until   = int(Utilities.swap(hex[:8]), 16)
            self.__elapsed = int(Utilities.swap(hex[8:16]), 16)
            self.distance = int(Utilities.swap(hex[16:24]), 16)
            self.calories = int(Utilities.swap(hex[24:28]), 16)
            self.maxSpeed = int(Utilities.swap(hex[32:40]), 16)/100
            self.maxHeartrate = int(Utilities.swap(hex[40:42]), 16)
            self.avgHeartrate = int(Utilities.swap(hex[42:44]), 16)
            self.minAltitude = int(Utilities.swap(hex[44:48]), 16)
            self.maxAltitude = int(Utilities.swap(hex[48:52]), 16)
            self.avgCadence = int(Utilities.swap(hex[52:56]), 16)
            self.maxCadence = int(Utilities.swap(hex[46:60]), 16)
            self.avgPower = int(Utilities.swap(hex[60:64]), 16)
            self.maxPower = int(Utilities.swap(hex[64:68]), 16)
            return self
        else:
            print hex
            raise GB500ParseException(self.__class__.__name__, len(hex), 96)
        
    def calculateDate(self, date):
        self.end = date + datetime.timedelta(milliseconds = (self.__until * 100))
        self.start = self.end - datetime.timedelta(milliseconds = (self.__elapsed * 100))
        self.duration = self.end - self.start
        
    def calculateCoordinates(self, trackpoints):
        relative_to_start = relative_to_end = {}
        
        for trackpoint in trackpoints:
            relative_to_start[abs(self.start - trackpoint.date)] = trackpoint
            relative_to_end[abs(self.end - trackpoint.date)] = trackpoint
            
        nearest_start_point = relative_to_start[min(relative_to_start)]
        nearest_end_point = relative_to_end[min(relative_to_end)]
    
        self.startPoint = Point(nearest_start_point.latitude, nearest_start_point.longitude)
        self.endPoint = Point(nearest_end_point.latitude, nearest_end_point.longitude)
        
# New class for just the header, the header packet is different.  
class TrackFileHeader(object):
    def __init__(self, index = 0, pointer = '', date = datetime.datetime.utcnow(), duration = datetime.timedelta(), distance = 0.0, trackpointCount = 0, lapCount = 0):
        self.index           = index
        self.pointer         = pointer
        self.date            = date
        self.duration        = duration
        self.distance        = distance
        self.trackpointCount = trackpointCount
        self.lapCount = lapCount
        #super(TrackFileHeader, self).__init__(date, duration,distance,trackpointCount)

    def __str__(self):
        return "%02i %s %05.1f %s %08i" % (self.index, self.date, self.distance, self.duration, self.trackpointCount)

    def fromHex(self, idx, hex, timezone=utc, units=""): 
        self.index           = idx
        self.date            = datetime.datetime(2000+int(hex[0:2], 16), int(hex[2:4], 16), int(hex[4:6], 16), int(hex[6:8], 16), int(hex[8:10], 16), int(hex[10:12], 16))
        self.trackpointCount = int(Utilities.swap(hex[12:16]), 16)
        self.duration        = datetime.timedelta(seconds=int(Utilities.swap(hex[16:24]), 16)/10)
        self.distance        = float(int(Utilities.swap(hex[24:32]), 16))
        self.lapCount        = int(hex[32:36], 16)
        self.pointer         = hex[36:40]

        # localize date
        self.date = timezone.localize(self.date)
        # todo support for imperial units
        if units == "imperial":
            self.distance = round(self.distance * 0.000621371, 1)
        else:
            self.distance = round(self.distance * 0.001, 1)
        return self
        
class TrackWithLaps(object):
    def __init__(self, date = datetime.datetime.utcnow(), duration = 0, distance = 0, calories = 0, topspeed = 0, climb = 0, trackpointCount = 0, lapCount = 0):
        self.date            = date
        self.duration        = duration
        self.distance        = distance
        self.calories        = calories
        self.topspeed        = topspeed
        self.climb           = climb
        self.trackpointCount = trackpointCount
        self.trackpoints     = []
        self.lapCount = lapCount
        self.laps = []
        #super(TrackWithLaps, self).__init__(date, duration,distance, calories, topspeed, climb, trackpointCount)
     
    def __getitem__(self, attr):
        return getattr(self, attr)

    def __str__(self):
        return "%s %08i %08i %08i %08i %08i %04i" % (self.date, self.distance, self.calories, self.topspeed, self.climb, self.trackpointCount, self.lapCount)
    
    def fromHex(self, hex, timezone=utc):
        if len(hex) == 128:
            self.date            = datetime.datetime(2000+int(hex[0:2], 16), int(hex[2:4], 16), int(hex[4:6], 16), int(hex[6:8], 16), int(hex[8:10], 16), int(hex[10:12], 16))
            self.trackpointCount = int(Utilities.swap(hex[12:16]), 16)
            self.duration        = datetime.timedelta(seconds=int(Utilities.swap(hex[16:24]), 16)/10)
            self.distance        = int(Utilities.swap(hex[24:32]), 16)
            self.lapCount        = int(Utilities.swap(hex[32:36]), 16)
            self.pointer         = hex[36:40]
            self.calories        = int(Utilities.swap(hex[48:52]), 16)
            self.topspeed        = int(Utilities.swap(hex[56:64]), 16)/100
            self.climb           = int(Utilities.swap(hex[68:72]), 16)

            # localize date and then convert to UTC
            self.date = timezone.localize(self.date).astimezone(utc)
            return self
        else:
            raise GB500ParseException(self.__class__.__name__, len(hex), 128)

    def addTrackpointsFromHex(self, hex):        
        trackpoints = Utilities.chop(hex, 64)
        for trackpoint in trackpoints: 
            #print trackpoint
            parsedTrackpoint = Trackpoint().fromHex(trackpoint)
            
            if not self.trackpoints:
                parsedTrackpoint.calculateDate(self.date)
            else:
                parsedTrackpoint.calculateDate(self.trackpoints[-1].date)
            self.trackpoints.append(parsedTrackpoint)
        
    def addLapsFromHex(self, hex):
        laps = Utilities.chop(hex,96)
        for lap in laps: 
            parsedLap = Lap().fromHex(lap)
            parsedLap.calculateDate(self.date)
            self.laps.append(parsedLap)

    def export(self, format, **kwargs):
        ef = ExportFormat(format)
        ef.exportTrack(self)

class ExportFormat(object):    
    def __init__(self, format):
        if os.path.exists(Utilities.getAppPrefix('exportTemplates', '%s.txt' % format)):
            
            templateConfig = ConfigParser.SafeConfigParser({
                'nicename':"%(default)s",
                'extension':"%(default)s",
                'hasMultiple': "false",
            })    
            templateConfig.read(Utilities.getAppPrefix('exportTemplates', 'formats.ini'))
            if not templateConfig.has_section(format):
                templateConfig.add_section(format)
            
            self.name        = format
            self.nicename    = templateConfig.get(format, 'nicename', vars={'default':format})
            self.extension   = templateConfig.get(format, 'extension', vars={'default':format})
            self.hasMultiple = templateConfig.getboolean(format, 'hasMultiple')
        else:
            self.logger.error('%s: no such export format' % format)
            raise ValueError('%s: no such export format' % format)
    
    def __str__(self):
        return "%s" % self.name
    
    def exportTrack(self, track, path, **kwargs):
        return self.__export([track], path, **kwargs)
    
    def exportTracks(self, tracks, path, **kwargs):
        if 'merge' in kwargs and kwargs['merge']:
            self.__export(tracks, path, **kwargs)
        else:
            for track in tracks:
                self.exportTrack(track, path, **kwargs)
    
    def __export(self, tracks, path, **kwargs):
        if os.path.exists(Utilities.getAppPrefix('exportTemplates', 'pre', '%s.py' % self.name)):
            sys.path.append(Utilities.getAppPrefix('exportTemplates', 'pre'))
            pre_processor = __import__(self.name)
            for track in tracks:
                pre_processor.pre(track)
        
        if not os.path.exists(path):
            os.mkdir(path)
            
        path = os.path.join(path, "%s.%s" % (tracks[0].date.strftime("%Y-%m-%d_%H-%M-%S"), self.extension))
        #first arg is for compatibility reasons
        t = Template.from_file(Utilities.getAppPrefix('exportTemplates', '%s.txt' % self.name))
        rendered = t.render(tracks = tracks, track = tracks[0])
        
        with open(path, 'wt') as f:
            f.write(rendered)
        return path

class GB500Exception():
    pass

class GB500SerialException(GB500Exception):
    pass

class GB500ParseException(GB500Exception):
    def __init__(self, what = None, length = None, expected = None):
        self.what = what
        self.length = length
        self.expected = expected

    def __str__(self):
        if self.what:
            return "Error parsing %s: Got %i, expected %i" % (self.what, self.length, self.expected) 
        else:
            return super(GB500ParseException, self).__str__()


def serial_required(function):
    def serial_required_wrapper(x, *args, **kw):
        try:
            x._connectSerial()
            return function(x, *args, **kw)
        except GB500SerialException, e:
            raise
        finally:
            x._disconnectSerial()
    return serial_required_wrapper

def connectToPC_required(function):
    def connectToPC_required_wrapper(x, *args, **kw):
        x._connectSerial()
        test = x._querySerial('0200017879')
        if test:
            return function(x, *args, **kw)
        else:
            print "Device is unresponsive.  Select 'CONNECT TO PC' from the device menu."
        x._disconnectSerial()

    return connectToPC_required_wrapper


class SerialInterface():
    _sleep = 0
    _port = ""
    
    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value
    
    def _connectSerial(self):
        """connect via serial interface"""
        if self.port == "":
            ports = list(list_ports.grep("0483:5740"))
            if len(ports) > 0:
                self.port = ports[0][0]
                self.logger.debug("USB virtual serial port found on " + self.port)
            else:
                self.port = self.config.get("serial", "comport")
                self.logger.debug("Virtual serial port not found. Reverting to config.ini: " + self.port)
        try:
            self.serial = serial.Serial(port=self.port, baudrate=self.config.get("serial", "baudrate"), timeout=self.config.getint("serial", "timeout"), xonxoff=0, rtscts=1)
            self.logger.debug("serial connection on " + self.serial.portstr)
        except serial.SerialException:
            self.logger.critical("error establishing serial connection")
            raise GB500SerialException
    
    def _disconnectSerial(self):
        """disconnect the serial connection"""
        self.serial.close()
        self.logger.debug("serial connection closed")
        time.sleep(self._sleep)
    
    def _writeSerial(self, command, *args, **kwargs):
        #try:
            if command in self.COMMANDS:
                hex = self.COMMANDS[command] % kwargs
            else:
                hex = command
            
            self.logger.debug("writing to serialport: %s" % hex)
            self.serial.write(Utilities.hex2chr(hex))
            #self.serial.sendBreak(2)
            time.sleep(self._sleep)
            #self.logger.debug("waiting at serialport: %i" % self.serial.inWaiting())
        #except:
        #    raise GB500SerialException

    def _read(self, size = 2070):
        data = Utilities.chr2hex(self.serial.read(size))
        #self.logger.debug("serial port returned: %s" % data if len(data) < 30 else "%s... (truncated)" % data[:30])
        self.logger.debug("serial port returned: %s" % data)
        return data

    def _readPayload(self):
	# find the payload and read the exact number of bytes 1 at a time
	# much faster than guessing at it and waiting for the timeout
	# byte by byte improves flow control/buffer overruns in linux	
        raw = ''
        data = Utilities.chr2hex(self.serial.read(3))
        if data:
            payload = int(data[2:6], 16)
            if payload > 0:
                for i in range (0, payload):
                    raw += self.serial.read()

            # read the last checksum byte
            raw += self.serial.read()
            
            data += Utilities.chr2hex(raw)
            self.logger.debug("serial port returned: %s" % data if len(data) < 30 else "%s... (truncated)" % data[:30])
            #self.logger.debug("serial port returned: %s" % data)
            return data
        else:
            return None
    def _querySerial(self, command, *args, **kwargs):
        self._writeSerial(command, *args, **kwargs)
        data = self._readPayload()
        return data
        
    def _diagnostic(self):
        """check if a connection can be established"""
        try:
            self._connectSerial()
            self._querySerial('whoAmI')
            self._disconnectSerial()
            self.logger.info("serial connection established successfully")
            return True
        except GB500SerialException:
            self.logger.info("error establishing serial port connection, please check your config.ini file")
            return False
    

class GB500(SerialInterface):
    """api for Globalsat GB580"""
    
    COMMANDS = {
        'getTracklist'                    : '0200017879',
        #'setTracks'                       : '02%(payload)s%(isFirst)s%(trackInfo)s%(from)s%(to)s%(trackpoints)s%(checksum)s', 
        #'getTracks'                       : '0200%(payload)s%(numberOfTracks)s%(trackIds)s%(checksum)s', 
        'getTracks'                       : '020005800100%(trackPtr)s%(checksum)s', 
        'requestNextTrackSegment'         : '0200018180', 
        'requestErrornousTrackSegment'    : '0200018283',
        'formatTracks'                    : '0200037900641E',
        'getWaypoints'                    : '0200017776',
        'setWaypoints'                    : '02%(payload)s76%(numberOfWaypoints)s%(waypoints)s%(checksum)s',
        'formatWaypoints'                 : '02000375006412',
        'unitInformation'                 : '0200018584',
        'whoAmI'                          : '020001BFBE',
        'unknown'                         : '0200018382'
        #'getSysConfig'                    : '02...86...',
        #'setSysConfig'                    : '02...96...',
        #'setSysInfo'                      : '02...98...',
        #'sendRoute'                       : '02...93...',
        #'deleteAllRoutes'                 : '02...97...',
        #'FINISH' =                        : '02...8A...',
        #'sendTrackStart' =                : '02...90...',
        #'sendTrackSection' =              : '02...91...',
    }
            
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        #look for a user specific config (presumably with api keys)    
        userConfigPath = appdirs.user_config_dir('CycloTrain')
        configFile = os.path.join(userConfigPath, 'config.ini') 
        if os.path.isfile(configFile):
                self.config.read(configFile)
        else:
            configFile = Utilities.getAppPrefix('config.ini')
            self.config.read(configFile)
        
        self.timezone = timezone(self.config.get('general', 'timezone')) 
        self.units = self.config.get("general", "units")
        self.apiKey = self.config.get("api_keys", "strava") if self.config.has_option('api_keys', 'strava') else None

        #logging http://www.tiawichiresearch.com/?p=31 / http://www.red-dove.com/python_logging.html
        handler = logging.FileHandler(Utilities.getAppPrefix('gb580.log'), mode='w')        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(lineno)d %(funcName)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)

        self.logger = logging.getLogger('GB500')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
                                    
        outputHandler = logging.StreamHandler()
        if self.config.getboolean("debug", "output"):
            level = logging.DEBUG
            format = '%(levelname)s %(funcName)s(%(lineno)d): %(message)s'
        else:
            level = logging.INFO
            format = '%(message)s'
        outputHandler.setFormatter(logging.Formatter(format))
        outputHandler.setLevel(level)
        self.logger.addHandler(outputHandler)
        
        #self._connectSerial()
        
        if self.__class__ is GB500:
            product = self.getProductModel()
            
            #downcasting to a specific model
            if product == "GB-580":
                self.__class__ = GB580
            #add more lines for cyclo and timex
      
    @serial_required
    def getProductModel(self):
        try:
            response = self._querySerial('whoAmI')
            watch = Utilities.hex2chr(response[6:-4])
            product, model = watch[:-1], watch[-1:]
            return product
        except GB500SerialException: #no response received, assuming command was not understood force default
            return "GB-580"
        
    @serial_required
    def testConnectivity(self):
        try:
            self._querySerial('whoAmI')
            return True
        except:
            return False
                                           
        
    def getExportFormats(self):
        formats = []
        
        for format in glob.glob(Utilities.getAppPrefix("exportTemplates", "*.txt")):
            (filepath, filename) = os.path.split(format)
            (shortname, extension) = os.path.splitext(filename)
            e = ExportFormat(shortname)
            formats.append(e)
        return formats
        
    @connectToPC_required
    def getTracklist(self):
        raise NotImplemented('This is an abstract method, please instantiate a subclass')

    def getAllTracks(self):
        headers = self.getTracklist()
        if headers:
            return [self.getTrack(header.pointer) for header in headers]

    @serial_required
    def getTrack(self, trackPtr):
        raise NotImplemented('This is an abstract method, please instantiate a subclass')
    
    def exportTrack(self, track, format = None, path = None, **kwargs):
        if format is None:
            format = self.config.get("export", "default")
        if path is None:
            path = os.path.abspath(Utilities.getAppPrefix(self.config.get('export', 'path')))
        
        ef = ExportFormat(format)
        return ef.exportTrack(track, path, **kwargs)
    
    def importTracks(self, files, **kwargs):        
        if "path" in kwargs:
            path = os.path.join(kwargs['path'])
        else:
            path = Utilities.getAppPrefix('import')
        
        tracks = []
        for file in files:
            with open(os.path.join(path,file)) as f:
                data = f.read()
                tracks.extend(self.__parseGpxTrack(data))
        
        self.logger.info('imported tracks %i' % len(tracks))
        return tracks
    
    def __parseGpxTrack(self, track):
        gpx = GPXParser(track)
        return gpx.tracks
    
    @connectToPC_required
    def setTracks(self, tracks):
        raise NotImplemented('This is an abstract method, please instantiate a subclass')

    @connectToPC_required
    def formatTracks(self):
        self._writeSerial('formatTracks')
        # wait for response
        while True:
            time.sleep(1)
            if self.serial.in_waiting  != 0:
                break
        response = self._read(4)
        if response == '79000000':
            self.logger.debug('format tracks successful')
            return True
        else:
            self.logger.error('format not successful')
            return False
        
    @connectToPC_required
    def getWaypoints(self):
        response = self._querySerial('getWaypoints')            
        waypoints = Utilities.chop(response[46:-2], 40) #trim junk 
        return [Waypoint().fromHex(waypoint) for waypoint in waypoints] 

    def exportWaypoints(self, waypoints, **kwargs):
        if 'path' in kwargs:
            filepath = os.path.join(kwargs['path'], 'waypoints.txt')
        else:    
            filepath = Utilities.getAppPrefix('waypoints.txt')
        
        template = Template.from_file(Utilities.getAppPrefix('waypoint_template.txt'))
        rendered = template.render(waypoints = waypoints)

        with open(filepath,'wt') as f:
            f.write(rendered)
            
        self.logger.debug('Successfully wrote waypoints to %s' % filepath)
        return filepath
    
    def importWaypoints(self, **kwargs):
        if 'path' in kwargs:
            filepath = os.path.join(kwargs['path'], 'waypoints.txt')
        else:
            filepath = Utilities.getAppPrefix('waypoints.txt')
                
        with open(filepath) as f:
            importedWaypoints = f.read()
    
        waypoints = []
        for waypoint in eval(importedWaypoints):
            waypoints.append(Waypoint(str(waypoint['latitude']), str(waypoint['longitude']), waypoint['altitude'], waypoint['title'], waypoint['type']))
            
        self.logger.debug('Successfully read %i waypoint(s) from file' % len(waypoints)) 
        return waypoints
    
    @connectToPC_required
    def setWaypoints(self, waypoints):                               
        waypointsConverted = ''.join([hex(waypoint) for waypoint in waypoints])
        numberOfWaypoints = Utilities.swap(Utilities.dec2hex(len(waypoints), 8))
        payload =  Utilities.dec2hex(5 + (20 * len(waypoints)), 4)
        checksum = Utilities.checkersum("%s76%s%s" % (str(payload), str(numberOfWaypoints), waypointsConverted))
        
        response = self._querySerial('setWaypoints', **{'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': waypointsConverted, 'checksum':checksum})
        
        if response[:6] == '760004':
            waypointsUpdated = int(Utilities.swap(response[6:10]), 16)
            self.logger.debug('waypoints updated: %i' % waypointsUpdated)
            return waypointsUpdated
        else:
            self.logger.error('error uploading waypoints')
            return False

    @connectToPC_required
    def formatWaypoints(self):
        self._writeSerial('formatWaypoints')
        while True:
            time.sleep(1)
            if self.serial.in_waiting  != 0:
                break
        response = self._read(4)
        if response == '75000000':
            self.logger.debug('deleted all waypoints')
            return True
        else:
            self.logger.error('deleting all waypoints failed')
            return False 

    @serial_required
    def getNmea(self):
        #http://regexp.bjoern.org/archives/gps.html
        #looks interesting
        #http://twistedmatrix.com/trac/browser/trunk/twisted/protocols/gps/nmea.py
        def dmmm2dec(degrees,sw):
            deg = math.floor(degrees/100.0) #decimal degrees
            frac = ((degrees/100.0)-deg)/0.6 #decimal fraction
            ret = deg+frac #positive return value
            if ((sw == "S") or (sw == "W")):
                ret=ret*(-1) #flip sign if south or west
            return ret
        
        line = ""
        while not line.startswith("$GPGGA"):
            self.logger.debug("waiting at serialport: %i" % self.serial.inWaiting())
            line = self.serial.readline()
            print line
        
        # calculate our lat+long
        tokens = line.split(",")
        lat = dmmm2dec(float(tokens[2]),tokens[3]) #[2] is lat in deg+minutes, [3] is {N|S|W|E}
        lng = dmmm2dec(float(tokens[4]),tokens[5]) #[4] is long in deg+minutes, [5] is {N|S|W|E}
        return lat, lng
    
    @serial_required
    def getUnitInformation(self):
        response = self._querySerial('unitInformation')
                
        if len(response) == 188:
            unit = {
                'device_name'      : Utilities.hex2chr(response[4:20]),
                'version'          : Utilities.hex2dec(response[50:52]),
                #'dont know'       : self.__hex2dec(response[52:56]),
                'firmware'         : Utilities.hex2chr(response[56:88]),
                'name'             : Utilities.hex2chr(response[90:110]),
                'sex'              : 'male' if (Utilities.hex2chr(response[112:114]) == '\x01') else 'female',
                'age'              : Utilities.hex2dec(response[114:116]),
                'weight_pounds'    : Utilities.hex2dec(response[116:120]),
                'weight_kilos'     : Utilities.hex2dec(response[120:124]),
                'height_inches'      : Utilities.hex2dec(response[124:128]),
                'height_centimeters' : Utilities.hex2dec(response[128:132]),
                'waypoint_count'   : Utilities.hex2dec(response[132:134]),
                'trackpoint_count' : Utilities.hex2dec(response[133:138]),
                'birth_year'       : Utilities.hex2dec(response[138:142]),
                'birth_month'      : Utilities.hex2dec(response[142:144])+1,
                'birth_day'        : Utilities.hex2dec(response[144:146])
            }
            return unit
        else:
            raise GB500ParseException('Unit Information', len(hex), 180)
            
    
class GB580(GB500):
    GB500.COMMANDS.update({
       'setTracks':     '02%(payload)s91%(trackInfo)s%(from)s%(to)s%(trackpoints)s%(checksum)s',
       'setTracksLaps': '02%(payload)s90%(trackInfo)s%(laps)s%(nrOfTrackpoints)s%(checksum)s'
    })
    
    @serial_required
    def getTracklist(self):
        tracklist = self._querySerial('getTracklist')
        if tracklist:
            trackHeaders = [] 
            if len(tracklist) > 8:
                j=1
                for hex in Utilities.chop(tracklist[6:-2],48):
                    header = TrackFileHeader().fromHex(j, hex, self.timezone, self.units)
                    j += 1
                    trackHeaders.append(header)
                self.logger.info('%i track(s) found' % len(trackHeaders))    
                return trackHeaders    
            else:
                self.logger.info('no tracks found') 
                pass
        else:
            print "Device is unresponsive.  Select 'CONNECT TO PC' from the device menu."

    @serial_required
    def getTrack(self, trackPtr):
        checksum = Utilities.checkersum("05800100%s" % (trackPtr))
        self._writeSerial('getTracks', **{'trackPtr':trackPtr, 'checksum':checksum})                    
        newtrack = None
        i = 0
        
        while True:
            data = self._readPayload()
            time.sleep(0)
            if data != '8A000000':

                #did we get a new train data session ?
                if len(data) == 136:
                    self.logger.debug('initalizing new track')
                    #save the old track if it exists and instantiate a new one
                    newtrack = TrackWithLaps().fromHex(data[6:-2], self.timezone)
                    i = 1

                #new laps data session is always after train header
                elif i == 1:
                    self.logger.debug('adding laps')
                    newtrack.addLapsFromHex(data[54:-2])
                    i = 2

                #new points data session?
                else:
                    self.logger.debug('adding trackpoints from new session')
                    newtrack.addTrackpointsFromHex(data[54:-2])

                # progress bars are nice
                progress = int(100 * len(newtrack.trackpoints)/newtrack.trackpointCount)
                bar = progress/2
                print '\r[{0}] {1}%'.format('#'*bar + '-'*(50-bar), progress),
                sys.stdout.flush()
                self._writeSerial('requestNextTrackSegment')

            else:
                #we are done, do maintenance work here
                if sys.platform == 'linux' or sys.platform == 'linux2':
                    os.system('setterm -cursor on')
                print
                for lap in newtrack.laps:
                    lap.calculateCoordinates(newtrack.trackpoints)
                    #self.logger.debug(lap)
                break        

        self.logger.debug('added 1 track')
        return newtrack
    
    @connectToPC_required
    def setTracks(self, tracks):        
        for track in tracks:
            lapChunk = hex(track)[:72 + (track.lapCount * 44)]
            
            response = self._querySerial(lapChunk)
            if response == '91000000' or response == '90000000':
                self.logger.info('uploaded lap information of track successfully')
            else:
                raise GB500Exception

            trackpointChunks = Utilities.chop(hex(track)[len(lapChunk):], 4152)
            for i, chunk in enumerate(trackpointChunks):
                response = self._querySerial(chunk)

                if response == '9A000000':
                    self.logger.info('successfully uploaded track')
                elif response == '91000000' or response == '90000000':
                    self.logger.debug("uploaded chunk %i of %i" % (i+1, len(trackpointChunks)))
                elif response == '92000000':
                    #this probably means segment was not as expected, resend previous segment?
                    self.logger.debug('wtf')
                else:
                    #print response
                    self.logger.info('error uploading track')
                    raise GB500Exception
        return len(tracks)
