import requests, gzip
#from tempfile import NamedTemporaryFile
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class stravaUploader(object):

    def __init__(self, filename = None, activity = None, name = None, description = None, private = False, trainer = False, commute = False, format = 'gpx', handle = None, apiKey = None):
        self.apiKey          = None
        self.reset()

        # turn off the warning because we're not checking the cert
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def reset(self, filename = None, activity = None, name = None, description = None, private = False, trainer = False, commute = False, format = 'gpx', handle = None):
        self.filename        = filename
        self._activity       = activity
        self.name            = name 
        self.description     = description 
        self.private         = private 
        self.trainer         = trainer  
        self.commute         = commute 
        self.format          = format 
        self.handle          = handle
        self.duplicate       = False
        self.uploadId        = None
        self._activityId     = None

    @property
    def url(self):
        return 'https://www.strava.com/api/v3/uploads'

    @property
    def activity(self):
        return self._activity

    @activity.setter
    def activity(self, value):
        possible = {'ride', 'run', 'swim', 'workout', 'hike', 'walk', 'nordicski', 'alpineski', 'backcountryski', 'iceskate', 'inlineskate', 'kitesurf', 'rollerski', 'windsurf', 'workout', 'snowboard', 'snowshoe', 'ebikeride', 'virtualride'} 
        if value.lower() in possible:
            self._activity = value
        else:
            raise TypeError("Invalid activity type")
 
    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, value):
        possible = {'fit', 'fit.gz', 'tcx', 'tcx.gz', 'gpx', 'gpx.gz'}
        if value.lower() in possible:
            self._format = value
        else:
            raise TypeError("Invalid file data type")

    @property
    def activityId(self):
        if self._activityId is None and self.apiKey is not None and self.uploadId is not None:
            headers = {'Authorization': 'Bearer ' + self.apiKey}
            r = requests.get(self.url + '/' + str(self.uploadId), headers=headers, verify=False).json()
            if r['activity_id'] is not None:
                self._activityId = r['activity_id']
        return self._activityId

    def upload(self):
        if self.apiKey is not None:
            headers = {'Authorization': 'Bearer ' + self.apiKey}

            if self.filename is not None:
                f = open(self.filename, 'rb')
                # gzip the file for performance 
                if self.format[-2:] != 'gz':
                    #cf = NamedTemporaryFile(suffix='.gz')
                    gzip.GzipFile(self.filename + '.gz', mode='w+b').writelines(f)               
                    files = {'file': open(self.filename + '.gz', 'rb')}
                    self._format +='.gz'
                else:
                    files = {'file': f}
                
            else: 
                raise Exception('Nothing to upload')

            params= {'data_type': self.format}

            if self.name is not None:
                params['name'] = self.name

            if self.activity is not None:
                params['activity_type'] = self.activity

            if self.private is not None:
                params['private'] = int(self.private)

            if self.trainer is not None:
                params['trainer'] = int(self.trainer)

            if self.commute is not None:
                params['commute'] = int(self.commute)

            if self.description is not None:
                params['description'] = self.description

            if self.handle is not None:
                params['external_id'] = self.handle

            res = requests.post(self.url, headers=headers, params = params, files=files, verify=False).json()
            # if we get an id we're almost home ...'
            if 'id' in res:
                self.uploadId = res['id']
                # ... but we still need to check for an error ...
                if res['error'] is not None:
                    error = res['error']
                    # ... usually this is a dupe but you never know
                    if 'duplicate' in error:
                        self.duplicate = True
                    else:
                        raise Exception('Strava error: ' + error)    

            # but the strava upload api never returns a happy 'message' 
            else:
                msg = 'APIv3 Upload Error.'
                if 'message' in res:
                    msg += ' ' + res['message']
                if 'errors' in res: 
                    msg += ' ' + res['errors'][0]['field'] + ' ' + res['errors'][0]['code']
                raise Exception(msg)
        else: 
            raise Exception('Api key is not set')
    