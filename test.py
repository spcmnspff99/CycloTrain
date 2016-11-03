import requests
import mmap
from requests_toolbelt import MultipartEncoder
headers = {
    'Authorization': 'Bearer 342db38ce31edd305d473f047f85261e3bfd561e',
}

file= open('export\\Afternoon_Ride.gpx', 'rb')
mmapped_file = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)

mpe = MultipartEncoder(fields={
#            'activity': self.activity,
#            'name': self.name,
#            'description': self.decscription,
#           'private': int(self.private),
#            'trainer': int(self.trainer),
#            'commute': int(self.commute),
            u'data_type': u'gpx',
#            'external_id': self.handle,
            u'file': ('Afternoon_Ride.gpx', mmapped_file,'text/xml')
            })

#filez = {
#    'activity_type': 'ride',
#    'file': mmapped_file_as_string,
#    'data_type': 'gpx'
#}

response = requests.post('https://www.strava.com/api/v3/uploads', headers=headers, data=mpe,verify=False)
print
print response
print
print response.json()



