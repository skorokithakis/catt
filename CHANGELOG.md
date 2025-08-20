# Changelog


## Unreleased

### Features

* Tell apart live videos from buffered videos (#464) [medape]


## [0.13.0](https://github.com/skorokithakis/catt/compare/v0.12.0...v0.13.0) (2025-08-19)


### Features

* Add swiergot's custom receiver ([b69af2f](https://github.com/skorokithakis/catt/commit/b69af2f3917182600b4174a938c9f3a14800645d))
* Add volumemute command ([#427](https://github.com/skorokithakis/catt/issues/427)) ([585b8d2](https://github.com/skorokithakis/catt/commit/585b8d2252475d94b0e693f1e45290815a251047))
* Tell apart live videos from buffered videos ([#464](https://github.com/skorokithakis/catt/issues/464)) ([7573736](https://github.com/skorokithakis/catt/commit/7573736dda091a425ae6f5daac43c33eac1b2154))


### Bug Fixes

* Allow use of info cmds on idle/inactive cc ([#345](https://github.com/skorokithakis/catt/issues/345)) ([cb9cf00](https://github.com/skorokithakis/catt/commit/cb9cf00e21a696cd6f3c916a0108e5dcfbda6562))
* Change DashCast app ID ([740a622](https://github.com/skorokithakis/catt/commit/740a62240a58c4b25770d3de79401376caa4c9ae))
* Don't do discovery dance when checking ip validity ([#309](https://github.com/skorokithakis/catt/issues/309)) ([5aa9467](https://github.com/skorokithakis/catt/commit/5aa9467ea6e2bd21ef0c5e4872e42bed0a8054fd))
* Fix casing issue with device names ([#375](https://github.com/skorokithakis/catt/issues/375)) ([#377](https://github.com/skorokithakis/catt/issues/377)) ([8a4103f](https://github.com/skorokithakis/catt/commit/8a4103f56f07af136db89426ade6a2315693f4ed))
* Fix crash while scanning (fixes [#368](https://github.com/skorokithakis/catt/issues/368)) ([fba58ad](https://github.com/skorokithakis/catt/commit/fba58ada7607d03f8d8ae2585c27e3e96c5e1f7a))
* Fix discovery function in the API ([#406](https://github.com/skorokithakis/catt/issues/406)) ([9cc0b09](https://github.com/skorokithakis/catt/commit/9cc0b09cb3d3048c757d14be3efb848e04638bdb)), closes [#405](https://github.com/skorokithakis/catt/issues/405)
* Fix importlib error on Python 3.8 and older ([#382](https://github.com/skorokithakis/catt/issues/382)) ([3ab2b8d](https://github.com/skorokithakis/catt/commit/3ab2b8d4c6608905467fef69feb782c5ba27a428))
* Fix issues with recent pychromecast / zeroconf ([#398](https://github.com/skorokithakis/catt/issues/398)) ([6c55414](https://github.com/skorokithakis/catt/commit/6c55414ebbdd0becfd69985c6df2745e4f19095b))
* Fix potential PyChromecast error by pinning to version 8 ([2cd4552](https://github.com/skorokithakis/catt/commit/2cd45525347258e52a89abec87d1a21cdb60f445))
* Include changelog in releases ([274df71](https://github.com/skorokithakis/catt/commit/274df718554943df6fb4657898a0a5a39924d70a))
* Make aliases case-insensitive (fixes [#366](https://github.com/skorokithakis/catt/issues/366)) ([e52394d](https://github.com/skorokithakis/catt/commit/e52394d0db42e5a6a5bb8e0e8d50cdbdf03ac23c))
* Pin Protobuf to &lt;4 to reduce incompatibilities (fixes [#394](https://github.com/skorokithakis/catt/issues/394)) ([0856a57](https://github.com/skorokithakis/catt/commit/0856a574f6b06f02e918ce0250f9ab8db79eba66))
* Pin PyChromecast and zeroconf (3rd-party dependency) to specific versions to avoid breakage ([1b31842](https://github.com/skorokithakis/catt/commit/1b3184262851f8e39f01ae3e6e94cc39d37c2b6c))
* Rework broken get_cast_with_ip ([#403](https://github.com/skorokithakis/catt/issues/403)) ([789ee2c](https://github.com/skorokithakis/catt/commit/789ee2cc70ff280a81d494e5e4a12086b06324e1))
* **save:** Replace cst.media_info with cst.cast_info in save function ([#441](https://github.com/skorokithakis/catt/issues/441)) ([a13b0fa](https://github.com/skorokithakis/catt/commit/a13b0faa6f442ab963c02f8db2b2ad51aeba9024))
* Set Poetry as the build-backend explicitly ([#433](https://github.com/skorokithakis/catt/issues/433)) ([0ff86b5](https://github.com/skorokithakis/catt/commit/0ff86b5f61a46134ea85e7fda615d585e303ca2a))
* Support PyChromecst 9 ([#325](https://github.com/skorokithakis/catt/issues/325)) ([31ba8ed](https://github.com/skorokithakis/catt/commit/31ba8edc8dba667a0ba2233c4aab5dad2ac18615))
* Switch to yt-dlp so YouTube and other services will work again ([#369](https://github.com/skorokithakis/catt/issues/369)) ([2955b5a](https://github.com/skorokithakis/catt/commit/2955b5ae3200f9fa6d14d85f97851ee0700ba29c))
* Update pychromecast requirement plus fixes ([#429](https://github.com/skorokithakis/catt/issues/429)) ([f335c13](https://github.com/skorokithakis/catt/commit/f335c130061103bbfc429adbc7b8c08af97bea45))
* Use yt-dlp rather than the defunct youtube-dl ([fe90975](https://github.com/skorokithakis/catt/commit/fe9097565767e255b146b5ad35f5a7486c5fa922))


### Documentation

* Add a note about firewalls to the readme ([#435](https://github.com/skorokithakis/catt/issues/435)) ([ef35ed3](https://github.com/skorokithakis/catt/commit/ef35ed34e1078d929377b71b4689f89eb7146370))

## v0.12.12 (2024-01-28)

### Fixes

* Set Poetry as the build-backend explicitly (#433) [Martin Weinelt]


## v0.12.11 (2023-05-09)

### Features

* Add volumemute command (#427) [neurodiv-eric]

### Fixes

* Update pychromecast requirement plus fixes (#429) [theychx]


## v0.12.10 (2023-01-30)

### Features

* Add swiergot's custom receiver. [Stavros Korokithakis]

### Fixes

* Change DashCast app ID. [Stavros Korokithakis]

* Fix discovery function in the API (#406) [Scott Moreau]


## v0.12.9 (2022-06-24)

### Fixes

* Rework broken get_cast_with_ip (#403) [theychx]


## v0.12.8 (2022-06-22)

### Fixes

* Fix issues with recent pychromecast / zeroconf (#398) [theychx]

* Pin Protobuf to <4 to reduce incompatibilities (fixes #394) [Stavros Korokithakis]


## v0.12.7 (2022-01-27)

### Fixes

* Fix importlib error on Python 3.8 and older (#382) [Emil Oppeln-Bronikowski]


## v0.12.6 (2022-01-15)

### Fixes

* Fix casing issue with device names (#375) (#377) [Lee]


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
# Changelog


## Unreleased

### Features

* Drop support for Python before 3.11, as that's what PyChromecast requires. [Stavros Korokithakis]


## v0.13.0 (2025-08-19)

### Features

* Tell apart live videos from buffered videos (#464) [medape]


## v0.12.12 (2024-01-28)

### Fixes

* Set Poetry as the build-backend explicitly (#433) [Martin Weinelt]


## v0.12.11 (2023-05-09)

### Features

* Add volumemute command (#427) [neurodiv-eric]

### Fixes

* Update pychromecast requirement plus fixes (#429) [theychx]


## v0.12.10 (2023-01-30)

### Features

* Add swiergot's custom receiver. [Stavros Korokithakis]

### Fixes

* Change DashCast app ID. [Stavros Korokithakis]

* Fix discovery function in the API (#406) [Scott Moreau]


## v0.12.9 (2022-06-24)

### Fixes

* Rework broken get_cast_with_ip (#403) [theychx]


## v0.12.8 (2022-06-22)

### Fixes

* Fix issues with recent pychromecast / zeroconf (#398) [theychx]

* Pin Protobuf to <4 to reduce incompatibilities (fixes #394) [Stavros Korokithakis]


## v0.12.7 (2022-01-27)

### Fixes

* Fix importlib error on Python 3.8 and older (#382) [Emil Oppeln-Bronikowski]


## v0.12.6 (2022-01-15)

### Fixes

* Fix casing issue with device names (#375) (#377) [Lee]


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


