import re
import json
import shlex
import base64
import secrets
import urllib3
import xmltodict
import subprocess
from random import *
from eyed3 import load
from datetime import datetime, timedelta
import defusedxml.ElementTree as ET


class Radiko():
    def __init__(self, args):
        """
        Initialize the Radiko class with user preferences and configurations.

        Args:
            version (str): Application version.
            station_id (str): Station ID to stream.
            area_free (bool): Whether the stream is unrestricted by area.
            time_free (bool): Whether time-shifted playback is allowed.
            start_time (str): Start time for time-shifted playback.
            end_time (str): End time for time-shifted playback.
            save (bool): Whether to save the stream as a file.
            output_dir (str): Directory to save output files.
        """
        
        self.args = args
        self.version = args.version
        self.station_id = args.station
        self.areafree = args.areaFree
        self.timefree = args.timeFree
        self.startTime = args.startTime
        self.endTime = args.endTime
        self.save = args.save
        self.output_dir = args.output_dir
        
        self.auth_key = self.get_Full_Key()
        self.user_id = self.get_User_ID()
        self.app, self.device, self.connection = self.get_platform_info()
        self.dateTime = self.get_Date()
        self.save_extension = 'mp3'
        
        self.urllib = urllib3.PoolManager()
    
    # Load a JSON file
    def load_json(self, file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
        
        return data
    
    # Generate a user ID
    def get_User_ID(self):
        length = 16
        user_id = secrets.token_hex(nbytes=length)
            
        return user_id
    
    # Get platform information
    def get_platform_info(self):
        app = 'aSmartPhone7o'
        device = 'Python.Radiko'
        connection = 'wifi'
        
        return app, device, connection
    
    # Retrieve the date and time
    def get_Date(self):
        dateTime_format = '%Y%m%d%H%M%S'
        dateTime = datetime.strptime(self.startTime, dateTime_format)
        
        return dateTime

    # Retrieve data of stations by region
    def get_Available_Stations(self) -> list:
        url = 'https://radiko.jp/v3/station/region/full.xml'
        
        available_stations = []
        request = self.urllib.request(method='GET', url=url)
        response = request.data.decode('utf-8')
        available_stations = xmltodict.parse(response)

        return available_stations

    # Get station information
    def get_station_info(self) -> dict:
        available_stations = self.get_Available_Stations()

        stations_data = available_stations['region']['stations']
        for data in stations_data:
            station_data = data['station']
            for station in station_data:
                id_data = station["id"]
                if id_data == self.station_id:
                    area_id = station["area_id"]
                    station_logo_url = station["banner"]
            
        return area_id, station_logo_url
    
    # Get GPS data
    def get_GPS(self, area_id) -> str:
        file_path = f'./data/json/area.json'
        COORDINATES_LIST = self.load_json(file_path)
        
        latitude = COORDINATES_LIST[area_id]['latitude']
        longitude = COORDINATES_LIST[area_id]['longitude']
        
        latitude = latitude + random() / 40.0 * (1 if (random() > 0.5) else -1)
        longitude = longitude + random() / 40.0 * (1 if (random() > 0.5) else -1)
        
        digits = 6
        latitude = str(round(latitude, digits))
        longitude = str(round(longitude, digits))
        
        coordinate = f'{latitude},{longitude},gps'
        
        return coordinate
    
    # Load the authentication key
    def get_Full_Key(self) -> str:
        file_path = f'./data/auth/auth_key.bin'
        
        with open(file_path, 'rb') as f:
            auth_key = f.read()
        auth_key = base64.b64encode(auth_key)
        
        return auth_key
    
    # Request for Auth1
    def access_Auth1(self, area_id):
        pattern = r'JP|^[1-47]$'
        if re.match(pattern, area_id) is None:
            raise TypeError('Invalid Area ID')
        
        url = 'https://radiko.jp/v2/api/auth1'
        
        headers={
            'X-Radiko-App' : self.app,
            'X-Radiko-App-Version' : self.version,
            'X-Radiko-Device' : self.device,
            'X-Radiko-User' : self.user_id
        }
        
        request = self.urllib.request(method='GET', url=url, headers=headers)
        auth1 = request
        
        return auth1
        
    # Get Partial key
    def access_Partial_Key(self, auth1):
        auth_key = base64.b64decode(self.auth_key)
        
        auth_token = auth1.getheader('x-radiko-authtoken')
        key_offset = int(auth1.getheader('x-radiko-keyoffset'))
        key_length = int(auth1.getheader('x-radiko-keylength'))
        
        partial_key = auth_key[key_offset : key_offset + key_length]
        partial_key = base64.b64encode(partial_key)
        
        return auth_token, partial_key
    
    # Request for Auth2
    def access_Auth2(self, auth_token, coordinate, partial_key):
        url = 'https://radiko.jp/v2/api/auth2'
        
        headers = {
            'X-Radiko-App' : self.app,
            'X-Radiko-App-Version' : self.version,
            'X-Radiko-AuthToken' : auth_token,
            'X-Radiko-Connection' : self.connection,
            'X-Radiko-Device' : self.device,
            'X-Radiko-Location' : coordinate,
            'X-Radiko-PartialKey' : partial_key,
            'X-Radiko-User' : self.user_id
        }
        
        request = self.urllib.request(method='GET', url=url, headers=headers)
        auth2 = request.data.decode('utf-8')
        
        return auth2

    # Authentication process
    def access_Authentication(self) -> str:
        area_id, station_logo_url = self.get_station_info()
        auth1 = self.access_Auth1(area_id=area_id)
        auth_token, partial_key = self.access_Partial_Key(auth1=auth1)
        coordinate = self.get_GPS(area_id=area_id)
        auth2 = self.access_Auth2(auth_token=auth_token, coordinate=coordinate, partial_key=partial_key)
        
        return auth_token
    
    # Get stream information
    def get_Stream_Info(self) -> dict:
        auth_token = self.access_Authentication()

        stream_info = {}
        stream_info['token'] = auth_token
        stream_info['url'] = f"https://radiko.jp/v2/api/ts/playlist.m3u8"

        if self.startTime and self.endTime:
            stream_info['url'] += f"?station_id={self.station_id}&l=15&ft={self.startTime}&to={self.endTime}"

        return stream_info
    
    # Get FFmpeg program file dir
    def get_Program_Path(self, cmd_name) -> str:
        if subprocess.getstatusoutput(f'type {cmd_name}')[0] == 0:
            return subprocess.check_output(f'which {cmd_name}', shell=True).strip().decode('utf8')
        else:
            print(f'{cmd_name} not found , install {cmd_name} ')
            exit()
    
    # Generate an FFmpeg command
    def get_FFmpeg_Command(self, FFmpeg_program, out_filename) -> str:
        stream_info = self.get_Stream_Info()
        print(f'stream_info: {stream_info}')
        input_url = stream_info['url']
        auth_token = stream_info['token']
        
        if FFmpeg_program == 'ffmpeg':
            program_path = self.get_Program_Path('ffmpeg')
            input_options = ''
            output_options = '-threads 8'
            cmd = f'"{program_path}" {input_options} -n -headers "X-Radiko-AuthToken: {auth_token}" -i "{input_url}" {output_options} "{out_filename}"'
        elif FFmpeg_program == 'ffplay':
            program_path = self.get_Program_Path('ffplay')
            cmd = f'{program_path} "{input_url}"'
        
        return cmd
    
    # Save the program
    def save_program(self):
        save_fime_name = f"{self.output_dir}/{self.save_extension}/{self.station_id}_{self.dateTime}.{self.save_extension}"
        
        save_cmd = self.get_FFmpeg_Command(FFmpeg_program='ffmpeg', out_filename=save_fime_name)
        save_cmd_split = shlex.split(save_cmd)
        process = subprocess.Popen(save_cmd_split)
        process.communicate()
        
