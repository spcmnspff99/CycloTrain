cyclotrain.pl - Portable script for interfacing with the globalsat GB580 family of devices

Credit where credit is due
---------------------------
This code borrows heavily and was branched from [speigei/gh615](https://github.com/speigei/gh615) fround on github.

Yet another special thanks goes to Globalsat themselves. They provided vital documentation without which this project would have floundered.  Also, I am a big fan of their products.

Some concepts were taken from the python stravalib project as far as the correct way to post to the strava API3 using the python requests library. There just isnt enough guidence in the api documentation itself and every other python project out there uploading tracks is using stravalib itslef.  I was relucatnt to inport starvalib as I only wanted to upload and didnt need the bloat that comes with all the entire api.  Its seemed too big for my little script.

This code is licensed under gpl3.

Name of the project
-------------------
My goal is to have a script that is OS portable and can interface with my timex cycle trainer 2.0 - cheifly to download tracks from this device and upload them to Strava.  While researching this, I learned that the device is actually manufactured by Globalsat and was originaly marketed as the GB580P.  The device was also licensed by Magelllan and sold as the Magellan/Mio Cyclo 105.  So the name of the project is a hybridization of the various names this device has been assigned under different branding.  I aim to write a script that can work with any of these devices.

Command Line
------------
The script remains CLI only - which makes it very fast.  There have been a number of improvements in this regard compared the original code and it is also very fast when you consider other gui tools that do this same thing, few as they may be. Also, It will run on any host os that can run python and has been tested on linux and windows.

Other things
------------
The script is able to detect the virtual serial port automatically and only uses the config.ini setting as a fallback.  This makes it particularly nice when switching between linux and windows as you really never have to fuss with config.ini.

With some minor modification and in most cases no modification whatsoever, all the original exports from the gh615 code work - this speaks to the skill of the original coder.  i.e. Nmea sentence, goolgle earth html, etc

I have added an option to upload the exported file(s) to strava automatically after the track is exported. This requires interfacing with the strava api3.  If this functionality is important to you, you will need an access token from strava and place it into the config.ini file under [api_keys].  Note, if you do place any sensitive information into this file please copy it to one of the following paths before you do for security reasons:

        windows: c:\users\<--YOURUSERNAME-->\AppData\Local\CycloTrain\Cyclotrain\
        linux: ~/.config/CycloTrain/
 
 You will need to create the CycloTrain directories. The script will check these folders for the config.ini file first and ignore the one in the current path if it finds it.  
 
 To obtain the strava acccess token, I have found the simplest way is to go to [the access token generator](//stravacli-dlenski.rhcloud.com) developed as part of the [stravacli toolset on GitHub](https://github.com/dlenski/stravacli).  If that site is ever down, there is a hack to get an access token manually and without a webserver.  Below, I lay out the steps I have taken in the past:

1.) Setup your strava account if you havent already. (The account does not have to be premium.)

2.) Log into your account from your browser to get a session.

3.) Now Create your own api aplication by pointing your browser to here: [https://www.strava.com/settings/api](https://www.strava.com/settings/api)
   
	Entries are sort of arbitrary in the form here's what I have:

	Application Name:  CycloTrain
	Website: http://www.google.com  ; must be any valid url
	Authorization Callback Domain: localhost ; better if its not valid domain

4.) Click to create.  You will see 3 fields at the top of the web page: Client ID, Client Secret, and Your Access Token.  This access token only grants read only and will not allow any uploads.  So copy the client ID and client secret and paste them into an empty test document and save. 

5.) Paste the client id into this url in a browser window:

	https://www.strava.com/oauth/authorize?client_id=<-- YOUR CLIENT ID HERE -->&response_type=code&redirect_uri=http://localhost/token_exchange&scope=write&state=mystate&approval_prompt=force

6.) You will see a web page with an Authorize button.  Click the botton and you will be directed to a non working webpage (i.e. your callback domain).  In the url address bar of this non working page, copy the auth code:

 	http://localhost/token_exchange?state=mystate&code=<-- YOUR AUTH CODE IS HERE -->

7.) From a terminal or cmd window run the following curl command after pasting in the appropriate information:

		curl -X POST https://www.strava.com/oauth/token \
		    -F client_id=<CLINETID> \
		    -F client_secret=<SECRET> \
		    -F code=<AUTH CODE>

8.) You will get a response in brackets similar to this:

	{"access_token":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","token_type":"Bearer","athlete":{"id":xxxxxxxx,"username":"xxxxxxxx","resource_state":3,"firstname":"xxxx","lastname":"xxxx","city":"xxxxxxxxxxxxxx","state":"xxxx","country":"United States","sex":"x","premium":false,"created_at":"xxxxxxxxxxxxxxxxxxxx","updated_at":"xxxxxxxxxxxxxxxxxxxx","badge_type_id":0,"profile_medium":"avatar/athlete/medium.png","profile":"avatar/athlete/large.png","friend":null,"follower":null,"follower_count":0,"friend_count":0,"mutual_friend_count":0,"athlete_type":0,"date_preference":"%m/%d/%Y","measurement_preference":"feet","clubs":[],"email":"xxxxx@xxxxxxxxxxx.xxx","ftp":null,"weight":null,"bikes":[],"shoes":[]}}
 
9.) Copy the access token from the response and save it somwhere with the client id and the client secret. The script will need this access token in order to upload data to strava on your behalf. Paste the access token into the config.ini file.
