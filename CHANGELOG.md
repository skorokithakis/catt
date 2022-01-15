# Changelog


## v0.12.5 (2021-12-19)

### Fixes

* Switch to yt-dlp so YouTube and other services will work again (#369) [anthonyrocom]


## v0.12.4 (2021-12-18)

### Fixes

* Fix crash while scanning (fixes #368) [Stavros Korokithakis]


## v0.12.3 (2021-12-10)

### Fixes

* Make aliases case-insensitive (fixes #366) [Stavros Korokithakis]

* Use yt-dlp rather than the defunct youtube-dl. [Stavros Korokithakis]


## v0.12.2 (2021-07-11)

### Fixes

* Pin PyChromecast and zeroconf (3rd-party dependency) to specific versions to avoid breakage. [Stavros Korokithakis]

* Allow use of info cmds on idle/inactive cc (#345) [theychx]

* Include changelog in releases. [Stavros Korokithakis]


## v0.12.1 (2021-02-27)

### Fixes

* Support PyChromecst 9 (#325) [theychx]

* Fix potential PyChromecast error by pinning to version 8. [Stavros Korokithakis]

* Don't do discovery dance when checking ip validity (#309) [theychx]


## v0.12.0 (2020-10-28)

### Features

* Add seek-to opt to cast cmd (#307) [theychx]

* Add remote-only subtitles to the API (#258) [Stavros Korokithakis]

### Fixes

* Wait longer for the Chromecast to connect to the HTTP server (#295) [Edd Barrett]


## v0.11.3 (2020-07-18)

### Fixes

* Fix spurious "Invalid byte range" error. [Stavros Korokithakis]


## v0.11.2 (2020-07-01)

### Fixes

* Revert to PyChromecast 6 until we can figure out what to do about 7. [Stavros Korokithakis]


## v0.11.1 (2020-06-29)

### Fixes

* Force pychromecast 7, update to new api. [Ian Calvert]

* Recognize the .jpeg suffix as a jpeg file (#262) [Stavros Korokithakis]

* Create parent directories if config dir doesn't exist (fixes #251) (#252) [Stavros Korokithakis]


## v0.11.0 (2020-03-01)

### Features

* Add cmds for config file manipulation (#240) [theychx]

* Add play_toggle cmd (#239) [theychx]

* Add force option to stop cmd (#238) [theychx]

* Add block option to cast cmd (#237) [theychx]

### Fixes

* Fix filename display (#244) [theychx]


## v0.10.3 (2020-01-26)

### Fixes

* Update PyChromecast requirement. [Stavros Korokithakis]


## v0.10.2 (2019-10-23)

### Fixes

* Add socket based fallback approach in get_local_ip. [Stavros Korokithakis]

* Add socket based fallback approach in get_local_ip. [theychx]

* Fix namespace related crash when using DashCast. [Stavros Korokithakis]

* Only serve files forever if it is necessary (#210) [Stavros Korokithakis]


## v0.10.0 (2019-08-19)

### Features

* Add ability to use subtitles with remote content (#207) [theychx]

* Add ability to use ip-address as device argument  (#197) [theychx]

### Fixes

* Adapt write_config to "new" get_chromecast (#208) [theychx]

* Try to eliminate spurious error msgs when seeking (#194) [theychx]


## v0.9.5 (2019-03-26)

### Fixes

* Only build py3 wheels/packages. [Stavros Korokithakis]


## v0.9.4 (2019-03-26)

### Fixes

* Make catt refuse to install under 2 more. [Stavros Korokithakis]


## v0.9.3 (2019-03-26)

### Fixes

* Refuse to install under Python 2. [Stavros Korokithakis]

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


