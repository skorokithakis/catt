# Changelog


## Unreleased

### Fixes

* Show better error message if Chromecast disconnects while playing. [Stavros Korokithakis]


## v0.9.0 (2019-01-20)

### Features

* Use new Youtube controller (#156) [theychx]

* Add stable API. [theychx]

### Fixes

* Make use of --ytdl-opt imply --force-default (#150) [theychx]


## v0.8.1 (2018-10-12)

### Features

* Use user specified format filter (#129) [theychx]

### Fixes

* Correct cast_site and write_config command names (#134) [theychx]

* Give correct error messages with Dashcast (#133) [theychx]


## v0.8.0 (2018-09-10)

### Features

* Add YouTube-DL option command line parameter. [Fatih Ka]

* Group support (#120) [theychx]

### Fixes

* Make save files portable (#125) [theychx]

* Fix "playing" never getting set (#113) [theychx]

* Fix ids and thumbnails not returned for active playlist entries (#112) [theychx]

* Make save restore more robust (#111) [theychx]

* Fail if a file given as a cli argument does not exist (#109) [theychx]

* Make cast_site accept stdin as argument (#108) [theychx]

* Make dashcast work with audio devices (#107) [theychx]


## v0.7.0 (2018-05-26)

### Features

* Cast a website to Chromecast (via DashCast) (#102) [Marcos Diez]

* Cast file with local or remote subtitles (#93) [Marcos Diez]

### Fixes

* Use netifaces instead of socket for get_local_ip (#100) [theychx]

* Guess the content type of remote files as well. [Samuel Loury]

* Specify the correct mimetype when casting local files (#96) [Marcos Diez]


## v0.6.1 (2018-05-05)

### Fixes

* Use a more educational example Youtube link (#92) [Ofek Lev]


## v0.6.0 (2018-04-30)

### Features

* Play random playlist entry (#86) [theychx]

* Save/restore (#84) [theychx]

### Fixes

* Improve kill (#85) [theychx]


## v0.5.7 (2018-04-10)

### Features

* Add force default option to cast command (#76) [theychx]

### Fixes

* Remove py2 compat code (#75) [theychx]


## v0.5.4 (2018-02-22)

### Fixes

* Misc improvements/fixes for final Python 2 release (#69) [theychx]


## v0.5.3 (2018-02-17)

### Fixes

* Make status command more useful (#65) [theychx]

* Proper fix for add action (#64) [theychx]

* Make info command more useful (#63) [theychx]


## v0.5.1 (2017-09-30)

### Features

* Make audio devices stream DASH-audio from YouTube (#49) [theychx]

* Add skip command (#43) [theychx]

* YouTube Queue support (#40) [theychx]

* Make scan fail when no cc's are found (#35) [theychx]

### Fixes

* Improve standard format (#54) [theychx]

* Ensure DIAL info from all CC's (#45) [theychx]

* Turn human_time into a def (#33) [theychx]


## v0.5.0 (2017-03-27)

### Features

* Make status use regular time descriptions (#32) [theychx]

* Add argument to volumeupdown (#29) [theychx]

* Add scanning for local Chromecasts. [Stavros Korokithakis]

### Fixes

* Further improve play_media (#31) [theychx]

* Rework CastController.init. [theychx]

* Do state_check in CastController.init. [theychx]

* Make check_state private. [theychx]

* Correct timeout parameter type. [theychx]

* Make catt work with pychromecast 0.8.0. [theychx]


## v0.4.3 (2017-03-14)

### Fixes

* Handle playlists better (fixes #24) [theychx]


## v0.4.2 (2017-02-18)

### Features

* Add aliases to config. (#19) [theychx]

* Switch to configparser for the config. [Stavros Korokithakis]

* Add custom time type for seek functions (#13) [theychx]

* Add config (#11) [theychx]

* Add user selectable CC device. [Stavros Korokithakis]

* Add user selectable CC device. [theychx]

### Fixes

* Freeze requirements until #12 is sorted (#20) [theychx]

* Replace connection message with more useful error message. (#18) [theychx]

* Cleanup in controllers / cli. (#17) [theychx]

* Change volume description (#16) [theychx]

* Remove volume default. (#15) [theychx]

* Make catt exit nicely if ytdl does not find a video. (#14) [theychx]

* Fail if a Chromecast cannot be found when writing the configuration. [Stavros Korokithakis]

* Small fix and comments in controllers.Cache. [theychx]

* Change cache filename and fix tempdir. [theychx]

* Simplify cache retrieval. [theychx]

* Weed out another auto-discovery edge case. [theychx]

* Solution for edge case where cc would not be auto-discovered. [theychx]

* Make test_catt.py pass (again) [theychx]

* Slight improvement of cache. [theychx]

* Make test_catt.py pass. [theychx]

* Stabilize cache handling. [theychx]

* Remove unnecessary code from play_media. [Stavros Korokithakis]


## v0.4.1 (2016-09-21)

### Fixes

* Add python3 compatible imports. [theychx]


## v0.4.0 (2016-09-20)

### Features

* Add local file casting support. [Stavros Korokithakis]


## v0.3.4 (2016-08-18)

### Features

* Add additional volume and info commands. [Stavros Korokithakis]


## v0.3.2 (2016-08-17)

### Fixes

* Speed up casting by not killing apps known to be nonblocking. [Stavros Korokithakis]


## v0.3.1 (2016-08-05)

### Fixes

* Find the best format from youtube-dl properly. [Stavros Korokithakis]


## v0.3.0 (2016-08-05)

### Features

* Add ability to fast forward and adjust volume. [Stavros Korokithakis]

### Fixes

* Pin to a different youtube-dl version (fixes #2). [Stavros Korokithakis]


## v0.2.0 (2016-05-30)

### Features

* Show title instead of URL when playing. [Stavros Korokithakis]

### Fixes

* Don't die on video URLs that point to the video file itself. [Stavros Korokithakis]

* Remove decimals from status time. [Stavros Korokithakis]

* Don't crash on status if nothing is playing. [Stavros Korokithakis]


## v0.1.4 (2016-04-25)

### Fixes

* Make the CLI interface more self-documenting. [Stavros Korokithakis]

* Fix rewind. [Stavros Korokithakis]


## v0.1.3 (2016-04-25)

### Fixes

* Fix setup.py crash due to missing history. [Stavros Korokithakis]


## v0.1.2 (2016-04-25)

### Fixes

* Fix version. [Stavros Korokithakis]


## v0.1.1 (2016-04-25)

### Fixes

* Don't crash on status if nothing is playing. [Stavros Korokithakis]

* Add option to delete cache. [Stavros Korokithakis]


## v0.1.0 (2016-04-25)

### Features

* Change the Chromecast stop command to kill. [Stavros Korokithakis]

* Add more commands. [Stavros Korokithakis]

### Fixes

* Make temporary directory finding cross-platform. [Stavros Korokithakis]

* Remove unused import. [Stavros Korokithakis]


