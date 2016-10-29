import sys, string, datetime, math
from xml.dom import minidom, Node

#http://the.taoofmac.com/space/blog/2005/10/11/2359
class GPXParser:
  def __init__(self, data, mode = 'file'):      
    self.tracks = []
    
    try:
      doc = minidom.parseString(data)
      doc.normalize()
    except:
      raise
      return # handle this properly later
    gpx = doc.documentElement    
    for node in gpx.getElementsByTagName('trk'):
      self.parseTrack(node)

  def calcDistance(self, lat1, lon1, lat2, lon2):                      
    nauticalMilePerLat = 60.00721
    nauticalMilePerLongitude = 60.10793
    rad = math.pi / 180.0
    milesPerNauticalMile = 1.15078
    metersPerNauticalMile = 1852.0
    
    yDistance = (lat2 - lat1) * nauticalMilePerLat
    xDistance = (math.cos(lat1 * rad) + math.cos(lat2 * rad)) * (lon2 - lon1) * (nauticalMilePerLongitude / 2)
    
    distance = math.sqrt( yDistance**2 + xDistance**2 )
    return int(distance * metersPerNauticalMile)

  def parseTrack(self, trk): 
    from gh600 import Track, TrackWithLaps, Trackpoint, Coordinate
        
    #default track
    track = TrackWithLaps()
    track.lapCount = 1

    for trkseg in trk.getElementsByTagName('trkseg'):
    
      if trkseg.getElementsByTagName('trkpt')[0].getElementsByTagName('time'):
          track.date = datetime.datetime.strptime(trkseg.getElementsByTagName('trkpt')[0].getElementsByTagName('time')[0].firstChild.data,'%Y-%m-%dT%H:%M:%SZ')
      
      timeToHere = track.date
      for i, trkpt in enumerate(trkseg.getElementsByTagName('trkpt')):          
          #default trackpoint
          trackpoint = Trackpoint()
          
          trackpoint.latitude = Coordinate(trkpt.getAttribute('lat'))
          trackpoint.longitude = Coordinate(trkpt.getAttribute('lon'))
          
          #setting defaults for non required elements
          if trkpt.getElementsByTagName('ele'):
             track.altitude = int(float(trkpt.getElementsByTagName('ele')[0].firstChild.data))
          
          if trkpt.getElementsByTagName('speed'):
             trackpoint.speed = int(float(trkpt.getElementsByTagName('speed')[0].firstChild.data))
             if trackpoint.speed > track.topspeed:
                 track.topspeed = trackpoint.speed
             
          if trkpt.getElementsByTagName('time'):
              time = datetime.datetime.strptime(trkpt.getElementsByTagName('time')[0].firstChild.data,'%Y-%m-%dT%H:%M:%SZ')
              difference = time - timeToHere
              timeToHere = time
              trackpoint.int = difference.seconds * 100
              track.duration += trackpoint.int
                        
          #calculate total distance
          if i > 0:
              #track.distance += self.calcDistance(trackpoint.latitude, trackpoint.longitude, track.trackpoints[len(track.trackpoints)-1]['latitude'], track.trackpoints[len(track.trackpoints)-1]['longitude'])
              track.distance += 1
          
          #add trackpoint to track
          track.trackpoints.append(trackpoint)
      track.trackpointCount = len(track.trackpoints)
    
    self.tracks.append(track)