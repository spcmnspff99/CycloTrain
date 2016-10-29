import math

def pre(track):    
    def formatdms(dec, lat):
        d, m = dec2dm(dec)
        
        ind = ('E', 'N')
        if d < 0:
            d = abs(d)
        ind = ('W', 'S')
        return '%d%.3f,%s' % (d, m, ind[lat])
    
    def dec2dm(dec):
        #http://home.online.no/~sigurdhu/Deg_formats.htm
        dec = float(dec)
        d = int(dec)
        m = (dec - d) * 60
        return (d, m)
    
    def nmeaChecksum(data):
        #http://schwehr.org/blog/archives/2006-03.html
        """ Take a NMEA 0183 string and compute the checksum"""
        if data[0]=='!' or data[0]=='?': data = data[1:]
        if data[-3]=='*': data = data[:-3]
        sum=0
        for c in data: sum = sum ^ ord(c)
        sumHex = "%x" % sum
        if len(sumHex)==1: sumHex = '0'+sumHex
        return sumHex
    
    for trackpoint in track.trackpoints:
        trackpoint.latitude_dms  = formatdms(trackpoint.latitude,1)
        trackpoint.longitude_dms = formatdms(trackpoint.longitude,0)
        trackpoint.status        = 'A' # information not available
        trackpoint.speed_knots   = trackpoint.speed * 0.539956803
        trackpoint.angle         = '000.0' # information not available
        trackpoint.magnetic      = '000.0,W' # information not available
        trackpoint.checksum      = nmeaChecksum('$GPRMC,'+trackpoint.status+','+str(trackpoint.date.strftime("%H%M%S"))+','+str(trackpoint.latitude_dms)+','+str(trackpoint.longitude_dms)+','+str(trackpoint.speed_knots)+','+str(trackpoint.angle)+','+str(trackpoint.date.strftime("%d%m%y"))+','+trackpoint.magnetic)