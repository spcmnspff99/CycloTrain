CycloTrain.pl - Portable script for interfacing with the globalsat GB580 family of devices

Credit where credit is due
---------------------------
This code borrows heavily and was branched from [speigei/gh615](https://github.com/speigei/gh615) found on github.

Yet another special thanks goes to Globalsat themselves. They provided vital documentation without which this project would have floundered.  Also, I am a big fan of their products.

Some concepts were taken from the python stravalib project as far as the correct way to post to the strava API3 using the python requests library. There just isnt enough guidence in the api documentation itself and every other python project out there uploading tracks is using stravalib itslef.  I was reluctant to import starvalib for this project as I only needed the upload feature and didnt need the bloat that comes with the entire api.  It just seemed too big for my little script.

This code is licensed under gpl3.

Requirements
------------
This code was written and tested on Python2.7.  There are plans to migrate to python3 but currently the code is only compatible with python2.

Required python modules:
appdirs, pyserial, pytz, requests

Windows:
You will need to install a [vitural com port driver.](http://www1.globalsat.com.tw/products-page_new.php?menu=2&gs_en_product_id=5&gs_en_product_cnt_id=34&img_id=469&product_cnt_folder=4)

Linux:
The device seems to work out of the box on most distros. It makes use of the cdc_acm module which should be preeloaded.  If not run this:

		$ sudo modprobe cdc_acm	

In the past, I have also blacklisted the cdc_acm module and loaded the pl2303 module instead. But this doesnt seem to be necessary.

To access the serial port as a non root user.  You will need to add the user to a specific user group, whichever one owns the device file.  For me that group was uucp.

		$ ls -la /dev/tty*
		
			crw-rw---- 1 root uucp 4, 65 Oct 31 19:41 /dev/ttyACM0

		$ sudo gpasswd --add username uucp


Name of the project
-------------------
My goal is to have a script that is OS portable and can interface with my timex cycle trainer 2.0 - cheifly to download tracks from this device and upload them to Strava.  While researching this, I learned that the device is actually manufactured by Globalsat and was originaly marketed as the GB580P.  The device was also licensed by Magelllan and sold as the Magellan/Mio Cyclo 105.  So the name of the project is a hybridization of the various names this device has been assigned under different branding.  My orignal goal was to write a script that can interface with all these devices.  However I have learned that the timex cycle trainer is running firmware that roughly equates to vey old firmware on the GB580p.  The data packets are slightly different and there would be substantial changes to the code to add the device.  Thus if you have this device I would suggest using the training peaks device agent software to flash it with [the latest gb580p firmware from glbalsat] (http://www1.globalsat.com.tw/products-page_new.php?menu=2&gs_en_product_id=5&gs_en_product_cnt_id=33&img_id=412&product_cnt_folder=4).  This is what I did while developing this script.  Along with making the device compatible with this script, this will also add some newer features, enhancements, and bug fixes.

Command line
------------
The script remains CLI only - which makes it very fast.  There have been a number of improvements in this regard compared the original code and it is also very fast when you consider other gui tools that do this same thing, few as they may be. Also, It will run on any host os that can run python and has been tested on linux and windows.

Other things
------------
With some minor modification and in most cases no modification whatsoever, all the original exports from the gh615 code work - this speaks to the skill of the original coder.  i.e. Nmea sentence, google earth html, etc.

The script is able to detect the virtual serial port automatically and only use the config.ini setting as a fallback.  This makes it particularly nice when switching between linux and windows as you really never have to fuss with config.ini.

There are two possible locations for the config.ini file. The default location is the local context from which the script is running. But there is also an option to store the file in a more secure location. The script will check this location first and ignore the local copy. Here are the location details per OS:

        windows: c:\users\<--YOURUSERNAME-->\AppData\Local\CycloTrain\Cyclotrain\
        linux: ~/.config/CycloTrain/

Any directory named "CycloTrain" will need to be created manually.

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
