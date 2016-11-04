import time, os
from stravaUploader import stravaUploader

if __name__ == "__main__":
    su = stravaUploader()
    su.filename = '/home/sean/build/CycloTrain/export/2016-10-30_19-35-19.gpx'
    su.format = 'gpx'
    su.private = True
    su.apiKey = '342db38ce31edd305d473f047f85261e3bfd561e'
    print 'uploading {} to strava'.format(os.path.basename(su.filename))
    su.upload()
    time.sleep(1)
    i=0
    print 'strava is processing the file ',
    while su.activityId is None:
        print '.',
        time.sleep(1)
    print 'done'
    print 'new activity_id: {}'.format(str(su.activityId))
    