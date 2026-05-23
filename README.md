VeloSyncGS.pl - Portable script for interfacing with the globalsat GB580 family of devices.

Credits
-------
This code was forked from https://code.google.com/archive/p/gh615/.

Special thanks goes to Globalsat for providing documentation on the extended packet definition beyond the capabilities of the gh-615.

The strava uploader library is taken from stravalib project - only the upload feature was needed.

Requirements
------------
Python 2.7
Required python modules:
appdirs, pyserial, pytz, requests

Windows:
You will need to install a [vitural com port driver.](http://www1.globalsat.com.tw/products-page_new.php?menu=2&gs_en_product_id=5&gs_en_product_cnt_id=34&img_id=469&product_cnt_folder=4)

Linux:
The device seems to work out of the box on most distros. It makes use of the cdc_acm module which should be preloaded.  But if not, run this:

		$ sudo modprobe cdc_acm	

You can also blacklist the cdc_acm module and load the pl2303 module instead if you have installed it. But this doesn't seem to be necessary.

To access the serial port as a non root user.  You will need to add the user to a specific user group, whichever one owns the device file.  For me that group was uucp.

		$ ls -la /dev/tty*
		
			crw-rw---- 1 root uucp 4, 65 Oct 31 19:41 /dev/ttyACM0

		$ sudo gpasswd --add username uucp


Device Compatibility
--------------------
The scripts have been tested using the Timex Cycle Trainer 2.0 - but only after flashing the device with the latest Globalsat 580p firmware. After this the device will boot up as the GB-580p. Compatibility with the Magellin/Mio Cyclo 105 is likely but has not been tested. Donor devices are welcome.

| Device | Status | Notes |
|--------|--------|-------|
| Timex Cycle Trainer 2.0 | ✅ Tested | Requires GB-580p firmware flash |
| Globalsat GB-580p | ✅ Tested | Native compatibility |
| Magellan/Mio Cyclo 105 | ⚠️ Likely Compatible | Not tested |

You'll need an old copy of Training Peaks/Timex device agent to flash the firmware.


Command Line
------------
There have been some speed enhancements during the track download. That and the CLI nature of the script makes it very fast. Also keeping the python in raw script form keeps it portable. There are no plans for GUI.

Working woth the prompt:  
  
.\VeloSync  
  
[l]  = get list of all tracks  
[a]  = export all tracks (to default format)  
[a?] = select format or [a <format>]  
[e]  = select and export tracks (to default format)  
[e?] = select format or [e <format>]  
[n]  = export newest track (to default format)  
[n?] = select format or [n <format>]  
  
[d]  = download waypoints  
[u]  = upload waypoints  
  
[X]  = erase all tracks  
[Z]  = erase all waypoints  
[i]  = get device information  
  
[q] = quit  

CLI Parameters:

.\VeloSync -n tcx  
.\VeloSync -l  
.\VeloSync -e2 gzp_ext  

Other Things
------------
The script is able to detect the virtual serial port automatically and only use the config.ini setting as a fallback.  This makes it particularly nice when switching between linux and windows as you really never have to fuss with config.ini.

There are two possible locations for the config.ini file

	./

or 
	linux: ~/.config/CycloTrain/
	windows: c:\users\<--YOURUSERNAME-->\AppData\Local\VeloSync

The script checks the user folder first.

Strava Upload
-------------
There is an option to upload the exported file(s) to strava automatically after the track is exported. This requires interfacing with the Strava api3. If this functionality is important to you, you will need to obtain an access token from Strava and place it into the config.ini file under [api_keys]. In this case, it is best to keep the entire config.ini file in the secure location for whichever OS you are running.

To obtain the strava acccess token, I have found the simplest way is to go to [the access token generator](https://stravacli-dlenski.rhcloud.com) developed as part of the [stravacli toolset on GitHub](https://github.com/dlenski/stravacli).  If that site is ever down, there is a hack to get an access token manually and without a webserver. Below, I lay out the steps I have taken in the past:

1.) Setup your strava account if you havent already. (The account does not have to be premium.)

2.) Log into your account from your browser to get a session.

3.) Create your own api application by pointing your browser here: [https://www.strava.com/settings/api](https://www.strava.com/settings/api). Entries are sort of arbitrary in the form, but here's what I have:

	Application Name:  CycloTrain
	Website: http://www.google.com  ; must be any valid url
	Authorization Callback Domain: localhost ; better if it's not a valid domain

4.) Click to create.  You will see 3 fields at the top of the web page: Client ID, Client Secret, and Your Access Token.  This access token only grants read only and will not allow any uploads.  So copy the client ID and client secret and paste them into an empty test document and save. 

5.) Paste the client id into this url in a browser window:

	https://www.strava.com/oauth/authorize?client_id=<--YOUR CLIENT ID HERE-->&response_type=code&redirect_uri=http://localhost/token_exchange&scope=write&state=mystate&approval_prompt=force

6.) You will see a web page with an Authorize button.  Click the botton and you will be directed to a non working webpage (i.e. your callback domain).  In the url address bar of this non working page, copy the auth code:

 	http://localhost/token_exchange?state=mystate&code=<--YOUR AUTH CODE IS HERE-->

7.) From a terminal or cmd window run the following curl command after pasting in the appropriate information:

		curl -X POST https://www.strava.com/oauth/token \
		    -F client_id=<CLIENTID> \
		    -F client_secret=<SECRET> \
		    -F code=<AUTH CODE>

8.) You will get a response in brackets similar to this:

	{"access_token":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","token_type":"Bearer","athlete":{"id":xxxxxxxx,"username":"xxxxxxxx","resource_state":3,"firstname":"xxxx","lastname":"xxxx","city":"xxxxxxxxxxxxxx","state":"xxxx","country":"United States","sex":"x","premium":false,"created_at":"xxxxxxxxxxxxxxxxxxxx","updated_at":"xxxxxxxxxxxxxxxxxxxx","badge_type_id":0,"profile_medium":"avatar/athlete/medium.png","profile":"avatar/athlete/large.png","friend":null,"follower":null,"follower_count":0,"friend_count":0,"mutual_friend_count":0,"athlete_type":0,"date_preference":"%m/%d/%Y","measurement_preference":"feet","clubs":[],"email":"xxxxx@xxxxxxxxxxx.xxx","ftp":null,"weight":null,"bikes":[],"shoes":[]}}
 
9.) Copy the access token from the response and save it somwhere with the client id and the client secret. The script will need this access token in order to upload data to strava on your behalf. Paste the access token into the config.ini file.
