def pre(track):    
    for trackpoint in track.trackpoints:
        trackpoint.timeFromStart = trackpoint.date - track.date