cyclotrain.pl - Portable script for interfacing with the globalsat GB580 family of devices

Credit where credit is due
---------------------------
This code borrows heavily and was branched from original code written by github user speigei for earlier generation Globalsat devices.
His original repository can be found here: https://github.com/speigei/gh615.

This code is licensed under gpl3.

Yet another special thanks goes to Globalsat themselves. They provided vital documentation without which this project would have floundered.  Also, I am a big fan of their products.

Name of the project
-------------------
My goal is to have a script that is OS portable and can interface with my timex cycle trainer 2.0 - cheifly to download tracks from this device and upload them to Strava.  While researching this, I learned that the device is actually manufactured by Globalsat and was originaly marketed as the GB580P.  The device was also licensed by Magelllan and sold as the Magellan/Mio Cyclo 105.  So the name of the project is a hybridization of the various names this device has been assigned under different branding.  I aim to write a script that can work with any of these devices.

Command Line
------------
The script remains CLI only - which makes it very fast.  There have been a number of improvements in this regard compared the original code and it is also very fast when you consider other gui tools that do this same thing, few as they may be. Also, It will run on any host os that can run python and has been tested on linux and windows.

Other things
------------
As an additional feature, the script is able to detect the port automatically and only use the config.ini setting as a fallback.  This makes it nice when switching between linux and windows.

With some minor modification and in most cases no modification whatsoever, all the original exports from the gh615 code work - this speaks to the skill of the original coder.  i.e. Nmea sentence, goolgle earth html, etc

I have added an option to upload the exported file(s) to strava automatically after the track is exported. This requires interfacing with the strava api 3.  If this functionality is important to you, you will need an api key from strava.  Here are some notes on setting this up:

The strava api is designed to exchange an access token with a web application. You have to grant any application script access to your data before it can upload or exchange data.  To do this in a traditional way, you would need to run a  web server and run code to handle this token exchange.  However it is stil possible to set this up with only a web browser and curl. Here are the steps I took to make that happen:

1.) Setup your strava account if you havent already. (The account does not have to be premium.)
2.) Log into your account from your browser to get a session.
3.) Now Create your own api aplication by pointing your browser to this url:

		https://www.strava.com/settings/api
   
    Entries are sort of arbitrary but here's what I have:

	Application Name:  CycloTrain
	Website: http://www.google.com  ; must be any valid url
	Authorization Callback Domain: localhost ; better if its not valid domain

4.) Click to create.  You will see 3 fields at the top of thr web page: Client ID, Client Secret, and Your Access Token.  This access token only grants read only and will not allow any uploads.  So copy the client ID and client secret and paste them into an empty test document and save. 

5.) Paste the client id into this url in a browser window:

https://www.strava.com/oauth/authorize?client_id=CLIENTID&response_type=code&redirect_uri=http://localhost/token_exchange&scope=write&state=mystate&approval_prompt=force


6.) You will see a web page with an Authorize button.  Click the botton and you will be directed to a non working webpage.  In the url address bar of this non working page, copy the code.  I.e. everything after "http://localhost/token_exchange?state=mystate&code=" 

7.) From a terminal or cmd window run the following curl command after pasting in the appropriate information:

		curl -X POST https://www.strava.com/oauth/token \
		    -F client_id=<CLINETID> \
		    -F client_secret=<SECRET> \
		    -F code=<code>

8.) You will get a respense in brackets similar to this:

{"access_token":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","token_type":"Bearer","athlete":{"id":xxxxxxxx,"username":"xxxxxxxx","resource_state":3,"firstname":"xxxx","lastname":"xxxx","city":"xxxxxxxxxxxxxx","state":"xxxx","country":"United States","sex":"x","premium":false,"created_at":"xxxxxxxxxxxxxxxxxxxx","updated_at":"xxxxxxxxxxxxxxxxxxxx","badge_type_id":0,"profile_medium":"avatar/athlete/medium.png","profile":"avatar/athlete/large.png","friend":null,"follower":null,"follower_count":0,"friend_count":0,"mutual_friend_count":0,"athlete_type":0,"date_preference":"%m/%d/%Y","measurement_preference":"feet","clubs":[],"email":"xxxxx@xxxxxxxxxxx.xxx","ftp":null,"weight":null,"bikes":[],"shoes":[]}}
 
9.) Copy the access token from the response and save it somwhere with the client id and the client secret. The script will need this access token in order to upload data to strava on your behalf. Paste the access token into the config.ini file.
