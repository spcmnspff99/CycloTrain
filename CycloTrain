#!/usr/bin/env python2

import glob, os, os.path, sys, time
import ConfigParser, appdirs
#from optparse import OptionParser
from argparse import ArgumentParser
from gb580 import GB500, ExportFormat
from Utilities import Utilities
from stravaUploader import stravaUploader

gb = GB500()

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

def prompt_format():
    print 'available export formats:'
    for format in gb.getExportFormats():
        print "[%s] = %s" % (format.name, format.nicename)

    format = raw_input("Choose output format: ").strip()
    return format

def upload_to_strava(format, filenames):
    uploaders = []
    if format == 'gpx_ext':
        format = 'gpx'
    for filename in filenames:
        print 'uploading {} to Strava'.format(os.path.basename(filename)),
        sys.stdout.flush()
        su = stravaUploader()
        su.apiKey = gb.apiKey
        su.format = format
        su.filename = filename
        su.private = False
        su.upload()
        if su.duplicate:
            print '- duplicate activity'
            sys.stdout.flush()
        else:
            print
            uploaders.append(su)

    if any(uploader.activityId is None for uploader in uploaders):
        if sys.platform == 'linux' or sys.platform == 'linux2':
            os.system('setterm -cursor off')
        print 'Strava is processing the file(s) ',
        sys.stdout.flush()
        while True:
            if any(uploader.activityId is None for uploader in uploaders):
                time.sleep(1)
                print '.',
                sys.stdout.flush()
            else:
                break
        print 'done'
        print "New activity_id(s):",
        for uploader in uploaders:
            print uploader.activityId,
        print
        if sys.platform == 'linux' or sys.platform == 'linux2':
            os.system('setterm -cursor on')

def choose():
    print """
What do you want to do?\n\
------TRACKS-------\n\
[l]  = get list of all tracks\n\
[a]  = export all tracks (to default format)\n\
[a?] = select format or [c <format>]\n\
[e]  = select and export tracks (to default format)\n\
[e?] = select format or [b <format>]\n\
[n]  = export newest track (to default format)\n\
[n?] = select format or [n <format>]\n\
-----WAYPOINTS-----\n\
[d]  = download waypoints\n\
[u]  = upload waypoints\n\
-----ETC-----------\n\
[X] = format tracks\n\
[Z] = format waypoints\n\
[i]  = get device information\n\
-------------------\n\
[q] = quit"""

    command = raw_input("=>").strip()

    if command == "l":
        print "Getting tracklist"
        tracklist()

    elif command.startswith("e"):
        print "Export track"
        headers = tracklist()
        if headers:
            pick = raw_input("enter track index ").strip()
            trackIndex = pick
            try:
                index = int(pick)
            except ValueError:
                    index = None
            if index > len(headers):
                raise IndexError
                index = None

            if command == "e?":
                format = prompt_format()
            elif command.startswith("e "):
                format = command[2:].strip()
            else:
                format = gb.config.get("export", "default")
                print "FYI: Exporting to default format '%s' (see config.ini)" % format

            track = gb.getTrack(headers[index-1].pointer)
            filenames = [(gb.exportTrack(track, format, merge = False))]
            if gb.apiKey is not None and format in {'tcx','gpx','gpx_ext'}:
                query = raw_input("upload to Strava? [Y/n] ").strip()
                if query[0:1].lower() != "n":
                    upload_to_strava(format, filenames)

    elif command.startswith("a"):
        print "Export all tracks"
        if command == "a?":
            format = prompt_format()
        elif command.startswith("a "):
            format = command[2:].strip()
        else:
            format = gb.config.get("export", "default")
            print "FYI: Exporting to default format '%s' (see config.ini)" % format

        tracks = gb.getAllTracks()
        if tracks:
            filenames = [(gb.exportTrack(track, format, merge = False)) for track in tracks]
            print 'exported %i tracks to %s' % (len(tracks), format)
            if gb.apiKey is not None and format in {'tcx','gpx','gpx_ext'}:
                query = raw_input("upload to Strava? [Y/n] ").strip()
                if query[0:1].lower() != "n":
                    upload_to_strava(format, filenames)

    elif command.startswith("n"):
        print "Export newest track"
        headers = gb.getTracklist()
        if headers:
            if command == "n?":
                format = prompt_format()
            elif command.startswith("n "):
                format = command[2:].strip()
            else:
                format = gb.config.get("export", "default")
                print "FYI: Exporting to default format '%s' (see config.ini)" % format

            headers.sort(key=lambda x: x.date)
            print 'exporting track from %s' % (headers[-1].date)
            track = gb.getTrack(headers[-1].pointer)
            filenames = [(gb.exportTrack(track, format, merge = False))]
            if gb.apiKey is not None and format in {'tcx','gpx','gpx_ext'}:
                query = raw_input("upload to Strava? [Y/n] ").strip()
                if query[0:1].lower() != "n":
                    upload_to_strava(format, filenames)

    elif command == "d":
        print "Download Waypoints"
        waypoints = gb.getWaypoints()
        results = gb.exportWaypoints(waypoints)
        print 'exported Waypoints to', results

    elif command == "u":
        print "Upload Waypoints"
        waypoints = gb.importWaypoints()        
        results = gb.setWaypoints(waypoints)
        print 'Successfully uploaded %i waypoint(s)' % results
        
    elif command == "X":
        warning = raw_input("warning, DELETING ALL TRACKS").strip()
        results = gb.formatTracks()
        print 'Deleted all Tracks:', results

    elif command == "Z":
        warning = raw_input("WARNING DELETING ALL WAYPOINTS").strip()
        results = gb.formatWaypoints()
        print 'Deleted all Waypoints:', results
    
    elif command == "i":
        unit = gb.getUnitInformation()
        print "* %s waypoints on device" % unit['waypoint_count']
        print "* %s trackpoints on device" % unit['trackpoint_count']

#    elif command == "x":
#        print prompt_format()

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
#        usage = 'usage: %prog arg [options]'
        description = 'Command Line Interface for GB-580 Python interface, for list of args see the README'
        parser = ArgumentParser(description=description)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-l", "--list", help="show a list of all tracks", dest="show", action="store_true")
        group.add_argument("-a", "--all", help="export all tracks", dest="all", action="store_true")
        group.add_argument("-n", "--new", help="export newest tracks", dest="new", action="store_true")
        parser.add_argument("-X", "--delete-tracks", help="delete all tracks", dest="dat", action="store_true")
        parser.add_argument("-Z", "--delete-waypoints", help="delete all waypoints", dest="daw", action="store_true")

        parser.set_defaults(
            merge  = False,
            input  = None,
            output = None,
        )
        parser.add_argument("-f", "--format", help="the format to export to (default: %s)" % gb.config.get('export','default'), dest="format", choices=[format.name for format in gb.getExportFormats()])
        parser.add_argument("-s", "--strava", help="upload to Strava", dest="strava", action="store_true")
        parser.add_argument("-p", "--com", help="the comport to use", dest="com" )

        parser.add_argument("-i", "--input", help="input file(s)", action="append", dest="input")
        parser.add_argument("-o", "--output", help="the path to output to", dest="output")

        options = parser.parse_args()

        if options.output:
            gb.config.set('export', 'path', options.output)

        if options.format:
            format = options.format

        if options.show:
            tracklist()
        elif options.all:
            print "export all tracks"
            if not format:
                format = gb.config.get("export", "default")
            tracks = gb.getAllTracks()
            if tracks:
                filenames = [(gb.exportTrack(track, format, merge = False)) for track in tracks]
                print 'exported %i tracks to %s' % (len(tracks), format)
                if options.strava:
                    if gb.apiKey is not None and format in {'tcx', 'gpx', 'gpx_ext'}:
                        upload_to_strava(format, filenames)
                    else:
                        print "missing api key or incompatible export format for Strava"
        elif options.new:
            print "export newest track"
            if not format:
                format = gb.config.get("export", "default")
            headers = gb.getTracklist()
            if headers:
                headers.sort(key=lambda x: x.date)
                print 'exporting track from %s' % (headers[-1].date)
                track = gb.getTrack(headers[-1].pointer)
                filenames = [(gb.exportTrack(track, format, merge = False))]
                print 'exported 1 track to %s' % (format)
                if options.strava:
                    if gb.apiKey is not None and format in {'tcx', 'gpx', 'gpx_ext'}:
                        upload_to_strava(format, filenames)
                    else:
                        print "missing api key or incompatible export format for Strava"

        if options.dat:
            warning = raw_input("warning, DELETING ALL TRACKS").strip()
            results = gb.formatTracks()

        if options.daw:
            warning = raw_input("warning, DELETING ALL WAYPOINTS").strip()
            results = gb.formatWaypoints()

        print

if __name__ == "__main__":
    main()
