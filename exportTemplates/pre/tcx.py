from gb580 import TrackWithLaps

#training center requires every workout to have at least one lap
#which contains all the trackpoints belonging to it

def pre(track):    
    if isinstance(track, TrackWithLaps):
        #loop through all trackpoints and check to which lap they belong to
        for trackpoint in track.trackpoints:            
            for lap in track.laps:
                if not hasattr(lap, 'trackpoints'):
                    lap.trackpoints = []
                    
                if trackpoint.date >= lap.start and trackpoint.date <= lap.end:
                    lap.trackpoints.append(trackpoint)
                    break
    else:
        #TODO
        pass
