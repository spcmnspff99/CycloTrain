import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class stravaUploader(object):

    def __init__(self, filename = None, activity = None, name = None, description = None, private = False, trainer = False, commute = False, format = 'gpx', handle = None, apiKey = None):
        self.filename        = filename
        self._activity       = activity
        self.name            = name 
        self.description     = description 
        self.private         = private 
        self.trainer         = trainer  
        self.commute         = commute 
        self.format          = format 
        self.handle          = handle
        self.apiKey          = apiKey
        self.uploadId       = None
        self._activityId     = None

        # turn off the warning because we're not checking the cert
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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
            raise TypeError("Invalid activity type.")
 
    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, value):
        possible = {'fit', 'fit.gz', 'tcx', 'tcx.gz', 'gpx', 'gpx.gz'}
        if value.lower() in possible:
            self._format = value
        else:
            raise TypeError("Invalid file data type.")

    @property
    def activityId(self):
        if self._activityId is None and self.apiKey is not None and self.uploadId is not None:
            headers = {'Authorization': 'Bearer ' + self.apiKey}
            response = requests.get(self.url + '/' + str(self.uploadId), headers=headers, verify=False).json()['activity_id']
            if response is not None:
                self._activityId = response 
        return self._activityId

    def upload(self):
        if self.apiKey is not None:
            headers = {'Authorization': 'Bearer ' + self.apiKey}

            if self.filename is not None:
                files = {'file': open(self.filename, 'rb')}
            #else: raise an exception

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

            response = requests.post(self.url, headers=headers, params = params, files=files, verify=False).json()
            self.uploadId = response['id']
        # else: raise exception