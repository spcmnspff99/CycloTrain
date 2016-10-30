import glob, os, sys
from optparse import OptionParser

from gb580 import GB500, ExportFormat
from Utilities import Utilities

gb = GB500()

def update_progress(progress):
    print '\r[{0}] {1}%'.format('#'*(progress/10), progress),
    
def tracklist():
    headers = gb.getTracklist()
    #display
    if headers:
        if gb.units == "imperial":
            print 'id            date            mi     ET     trkpnts'
        else:
            print 'id            date            km     ET     trkpnts'
        for track in headers:
            print str(track)
        return headers
    else:
        print 'no tracks found'
    pass

def prompt_format():
    print 'available export formats:'
    for format in gb.getExportFormats():
        print "[%s] = %s" % (format.name, format.nicename)
    
    format = raw_input("Choose output format: ").strip()
    return format
        

def choose():
    print """
What do you want to do?\n\
------TRACKS-------\n\
[a]  = get list of all tracks\n\
[b]  = select and export tracks (to default format) | [b?] to select format or [b <format>]\n\
[c]  = export all tracks (to default format)        | [c?] to select format or [c <format>]\n\
[d]  = upload tracks\n\
-----WAYPOINTS-----\n\
[e]  = download waypoints\n\
[f]  = upload waypoints\n\
-----ETC-----------\n\
[gg] = format tracks\n\
[hh] = format waypoints\n\
[i]  = get device information\n\
-------------------\n\
[q] = quit"""

    command = raw_input("=>").strip()
    
    if command == "a":
        print "Getting tracklist"
        tracklist()
    
    elif command.startswith("b"):
        print "Export track"
        
        if command.startswith("b!"):
            command = command[0] + command[2:]
        else:
            headers = tracklist()
        
        pick = raw_input("enter track index ").strip()
        #adds the slice notation for selecting tracks, i.e. [2:4] or [:-4] or [3]
        #if ":" in picks:
        #    lower, upper = picks.split(':')
        #    try:
        #        lower = int(lower)
        #    except ValueError:
        #        lower = None
        #    try:
        #        upper = int(upper)
        #    except ValueError:
        #        upper = None

        #    trackIds = gb.getAllTrackIds()[lower:upper]
        #elif "-" in picks:
        #    trackIds = [gb.getAllTrackIds()[int(picks)]]
        #else:
        #    trackIds = picks.split(' ')

        trackIndex = pick
        try:
            index = int(pick)
        except ValueError:
                index = None
        if index > len(headers):
            raise IndexError
            index = None
   
        if command == "b?":
            format = prompt_format()
        elif command.startswith("b "):
            format = command[2:].strip() 
        else:
            format = gb.config.get("export", "default")
            print "FYI: Exporting to default format '%s' (see config.ini)" % format
        
        ef = ExportFormat(format)
        merge = False
        #if ef.hasMultiple and len(trackIds) > 1:
        #    merge = raw_input("Do you want to merge all tracks into a single file? [y/n]: ").strip()
        #    merge = True if merge == "y" else False
        #print headers[index-1].pointer       
        #print "Retreiving track %s" % index
        track = gb.getTracks(headers[index-1].pointer)
        
        gb.exportTracks(track, format, merge = merge)
                

    elif command.startswith("c"):
        print "Export all tracks"
        if command == "c?":
            format = prompt_format()
        elif command.startswith("c "):
            format = command[2:].strip() 
        else:
            format = gb.config.get("export", "default")
            print "FYI: Exporting to default format '%s' (see config.ini)" % format
        
        tracks = gb.getAllTracks()
        results = gb.exportTracks(tracks, format)
        print 'exported %i tracks to %s' % (len(tracks), format)
        
    elif command == "d":
        print "Upload Tracks"
        files = glob.glob(os.path.join(Utilities.getAppPrefix(), "import", "*.gpx"))
        for i,format in enumerate(files):
            (filepath, filename) = os.path.split(format)
            #(shortname, extension) = os.path.splitext(filename)
            print '[%i] = %s' % (i, filename)
        
        fileId = raw_input("enter number(s) [space delimited] ").strip()
        fileIds = fileId.split(' ');
        
        filesToBeImported = []
        for fileId in fileIds:
            filesToBeImported.append(files[int(fileId)])
                    
        tracks = gb.importTracks(filesToBeImported)        
        results = gb.setTracks(tracks)
        print 'successfully uploaded tracks ', str(results)
        
    elif command == "e":
        print "Download Waypoints"
        waypoints = gb.getWaypoints()    
        results = gb.exportWaypoints(waypoints)
        print 'exported Waypoints to', results
        
    elif command == "f":
        print "Upload Waypoints"
        waypoints = gb.importWaypoints()        
        results = gb.setWaypoints(waypoints)
        print 'Imported %i Waypoints' % results
        
    elif command == "gg":
        print "Delete all Tracks"
        warning = raw_input("warning, DELETING ALL TRACKS").strip()
        results = gb.formatTracks()
        print 'Deleted all Tracks:', results
        
    elif command == "hh":
        print "Delete all Waypoints"
        warning = raw_input("WARNING DELETING ALL WAYPOINTS").strip()
        results = gb.formatWaypoints()
        print 'Formatted all Waypoints:', results
    
    elif command == "i":
        unit = gb.getUnitInformation()
        print "* %s waypoints on watch" % unit['waypoint_count']
        print "* %s trackpoints on watch" % unit['trackpoint_count']
    
    elif command == "x":
        print prompt_format()
    
    elif command == "q":
        sys.exit()
        
    else:
        print "whatever"
    
    choose()


def main():  
    #use standard console interface
    if not sys.argv[1:]:
        choose()
    #parse command line args
    else:
        usage = 'usage: %prog arg [options]'
        description = 'Command Line Interface for GB-580 Python interface, for list of args see the README'
        parser = OptionParser(usage, description = description)
        #parser.add_option("-a", "--tracklist", help="output a list of all tracks")
        #parser.add_option("-b", "--download-track")
        #parser.add_option("-c", "--download-all-tracks")
        #parser.add_option("-d", "--upload-track")
        #parser.add_option("-e", "--download-waypoints")
        #parser.add_option("-f", "--upload-waypoints")  
        #parser.add_option("-gg","--format-tracks") 
        #parser.add_option("-h", "--connection-test")
        #parser.add_option("-i", "--unit-information") 
        
        parser.set_defaults(
            format = "gpx",
            merge  = False,
            input  = None,
            output = None,
        )
        
        parser.add_option("-t", "--track", help="a track id",  action="append", dest="tracks", type="int")
        parser.add_option("-f", "--format", help="the format to export to (default: %s)" % gb.config.get('export','default'), dest="format", choices=[format.name for format in gb.getExportFormats()])
        parser.add_option("-m", "--merge", help="merge into single file?", dest="merge", action="store_true")
        parser.add_option("-c", "--com", dest="com",  help="the comport to use")
        parser.add_option("-v", "--firmware", dest="firmware", choices=["1","2"], help="firmware version of your GH: (1 for old, 2 for new)")
        
        
        parser.add_option("-i", "--input", help="input file(s)", action="append", dest="input")
        parser.add_option("-o", "--output", help="the path to output to", dest="output")
        
        (options, args) = parser.parse_args()
        
        if len(args) != 1:
            parser.error("incorrect number of arguments")
        
        #set firmware version
        if options.firmware:
            gb.config.set('general', 'firmware', int(options.firmware))
        
        #set serial port
        if options.com:
            gb.config.set('serial', 'comport', options.com)

        if options.output:
            gb.config.set('export', 'path', options.output)
            
        if options.format:
            gb.config.set('export', 'default', options.format)
        
        if args[0] == "a":
            tracklist()
            
        elif args[0] == "b":            
            if not options.tracks:
                parser.error("use option '--track' to select track")
                
            tracks = gb.getTracks(options.tracks)
            gb.exportTracks(tracks, gb.config.get('export', 'default'), gb.config.get('export', 'path'), merge = options.merge)
            
        elif args[0] == "c":        
            tracks = gb.getAllTracks()
            gb.exportTracks(tracks, gb.config.get('export', 'default'), gb.config.get('export', 'path'), merge = options.merge)
            
        elif args[0] == "d":
            if not options.input:
                parser.error("use option '--input' to select files")
            tracks = gb.importTracks(options.input)
            results = gb.setTracks(tracks)
        
        elif args[0] == "e":
            waypoints = gb.getWaypoints()    
            results = gb.exportWaypoints(waypoints, path=options.output)
            
        elif args[0] == "f":
            waypoints = gb.importWaypoints(path=options.input[0])
            results = gb.setWaypoints(waypoints)
            print 'Imported Waypoints %i' % results
            
        elif args[0] == "gg":
            warning = raw_input("warning, DELETING ALL TRACKS").strip()
            results = gb.formatTracks()
            
        elif args[0] == "hh":
            warning = raw_input("warning, DELETING ALL WAYPOINTS").strip()
            results = gb.formatWaypoints()
                    
        elif args[0] == "i":
            return gb.getUnitInformation()
        
        else:
            parser.error("invalid argument, try -h or see README for help")
    
        
if __name__ == "__main__":
    main()
