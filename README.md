# Radiko-Downloader

Radiko-Downloader can record the [radiko.jp](https://radiko.jp/) programs outside of Japan.

```console
Radiko-Downloader
 ┣ data
 ┃ ┣ auth
 ┃ ┃ ┗ auth_key.bin
 ┃ ┣ json
 ┃ ┃ ┗ area.json
 ┣ utils
 ┃ ┣ __init__.py
 ┃ ┗ str2bool.py
 ┣ LICENSE
 ┣ README.md
 ┣ main.py
 ┣ radiko_urllib3.py
 ┗ requirements.txt
```

## Warning

**Please do not use this project for commercial use. Only for your personal, non-commercial use.**

## Technologies

- `Python` : 3.9

# Technical Details

The authentication of PC(html5) version radkio validates user's location via IP address.

However, the android version of radkio validates user provided by GPS information, not via user's IP address.

# Getting Started

## Installation

- You can install it **locally:**
  ```console
  $ git clone https://github.com/devhaaana/radiko-downloader.git
  $ cd radiko-downloader
  ```

## Parameters

* `version` : Version of the application

  * default: `1.0.0`
* `station` : Stream Station ID (e.g., TBS, LFR)

  * default: `TBS`
* `areaFree` : Whether the stream is area-free

  * default: `False`
* `timeFree` : Whether the stream is time-free

  * default: `False`
* `startTime` : Stream start time (format: YYYYMMDDHHMM)

  * default: `None`
* `endTime` : Stream end time (format: YYYYMMDDHHMM)

  * default: `None`
* `Save` : Whether to save the stream as a file

  - default: `False`
* `output_dir` : Directory to save output files

  - default: `./data`

## Usage

```console
python main.py --version=1.0.0 --station=LFR --areaFree=False --timeFree=True --startTime=20241106010000 --endTime=20241106030000 --save=True --output_dir=./data
```

## Reference

[rajiko](https://github.com/jackyzy823/rajiko)
