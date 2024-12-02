import re
import json
import shlex
import base64
import secrets
import requests
import subprocess
from random import *
from eyed3 import load
from datetime import datetime, timedelta
import defusedxml.ElementTree as ET
import xmltodict


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
        self.save_extension = 'mp3'
    
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

    # Retrieve the current date and time
    def get_Date(self):
        now = datetime.now()
        date_format = '%Y%m%d'
        
        if now.hour < 5:
            current_date = (now - timedelta(days=1)).strftime(date_format)
        else:
            current_date = now.strftime(date_format)
            
        time_format = '%Y%m%d%H0000'
        current_time = datetime.now().strftime(time_format)
        
        return current_date, current_time

    # Retrieve program information
    def get_Program_Info(self):
        current_date, current_time = self.get_Date()
        
        url = f'https://radiko.jp/v3/program/station/date/{current_date}/{self.station_id}.xml'
        
        response: requests.Response = requests.get(url)
        response_element = ET.fromstring(response.text)
        
        for station in response_element.findall(".//station"):
            station_name = station.findtext('name')
            for program in station.findall(".//prog"):
                program_ft = program.get("ft")
                program_to = program.get("to")
                program_title = program.findtext('title', default='No Title')
                
                if program_ft is not None and program_to is not None and program_title is not None:
                    try:
                        if program_ft <= current_time < program_to:
                            program_pfm = program.findtext('pfm', default='No Performer')
                            program_logo = program.findtext('img', default='No img URL')
                            break
                    except ValueError as e:
                        print(f"Error comparing time: {e}")
        
        program_information = {
            'station_id' : self.station_id,
            'station_name' : station_name,
            'program_date' : current_date,
            'program_title' : program_title,
            'program_performer' : program_pfm,
            'program_logo_url' : program_logo,
        }
        
        return program_information
    
    # Retrieve data of stations by region
    def get_Available_Stations(self) -> list:
        url = 'https://radiko.jp/v3/station/region/full.xml'
        
        available_stations = []
        response: requests.Response = requests.get(url)
        available_stations = xmltodict.parse(response.text)
                
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
        
        auth1: requests.Response = requests.get(url=url, headers=headers)
        auth1.raise_for_status()
        
        return auth1
        
    # Get Partial key
    def access_Partial_Key(self, auth1):
        auth_key = base64.b64decode(self.auth_key)
        
        auth_token = auth1.headers.get('X-Radiko-AuthToken')
        key_offset = int(auth1.headers.get('X-Radiko-KeyOffset'))
        key_length = int(auth1.headers.get('X-Radiko-KeyLength'))
        
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
        
        auth2: requests.Response = requests.get(url=url, headers=headers)
        auth2.raise_for_status()
        
        return auth2

    # Authentication process
    def access_Authentication(self) -> str:
        area_id, station_logo_url = self.get_station_info()
        auth1 = self.access_Auth1(area_id=area_id)
        auth_token, partial_key = self.access_Partial_Key(auth1=auth1)
        coordinate = self.get_GPS(area_id=area_id)
        auth2 = self.access_Auth2(auth_token=auth_token, coordinate=coordinate, partial_key=partial_key)
        
        return auth_token
    
    # Retrieve the streaming URL
    def get_Create_URL(self) -> str:
        url = f'https://radiko.jp/v3/station/stream/{self.app}/{self.station_id}.xml'
        
        base_url = []
        
        response: requests.Response = requests.get(url)
        response = xmltodict.parse(response.text)
        stream_url = response['urls']['url'][-1]['playlist_create_url']
            
        return stream_url
    
    # Retrieve the streaming M3U8 URL
    def get_Stream_M3U8_URL(self, url, auth_token) -> str:
        headers = {
            'X-Radiko-AuthToken' : auth_token,
        }
        
        response: requests.Response = requests.get(url=url, headers=headers)
        body = response.text
        
        pattern = r'^https?://.+m3u8'
        lines = re.findall(pattern, body, flags=(re.MULTILINE))
        response.raise_for_status()
        
        return lines[0]
    
    # Get stream information
    def get_Stream_Info(self) -> dict:
        stream_info = {}
        auth_token = self.access_Authentication()
        create_url = self.get_Create_URL()
        
        stream_info['token'] = auth_token
        if (self.startTime == None) and (self.endTime == None):
            stream_info['url'] = f'{create_url}?station_id={self.station_id}&l=15'
        else:
            stream_info['url'] = f'{create_url}?station_id={self.station_id}&l=15&ft={self.startTime}&to={self.endTime}'
            
        url = stream_info['url']
        chunk_url = self.get_Stream_M3U8_URL(url=url, auth_token=auth_token)
        stream_info['url'] = chunk_url
        
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
        program_information = self.get_Program_title()
        program_date = program_information['program_date']
        program_title = program_information['program_title']
        save_fime_name = f"{self.output_dir}/{self.save_extension}/{self.station_id}_{program_title}_{program_date}.{self.save_extension}"
        
        save_cmd = self.get_FFmpeg_Command(FFmpeg_program='ffmpeg', out_filename=save_fime_name)
        save_cmd_split = shlex.split(save_cmd)
        process = subprocess.Popen(save_cmd_split)
        process.communicate()
        
        mp3_tag = self.set_mp3_Meta_Tag(file_path=save_fime_name, program_information=program_information)
        
        return ''
    
    # Set mp3 file meta tag
    def set_mp3_Meta_Tag(self, file_path, program_information):
        station_id = program_information['station_id']
        station_name = program_information['station_name']
        program_date = program_information['program_date']
        program_title = program_information['program_title']
        program_performer = program_information['program_performer']
        program_logo_url = program_information['program_logo_url']
        
        audiofile = load(file_path)
        
        response = requests.get(program_logo_url)
        imagedata = response.content
        audiofile.tag.images.set(3, imagedata, 'image/png', u'Description')
        
        audiofile.tag.title = program_title
        audiofile.tag.artist = program_performer
        audiofile.tag.album = f'{program_title} {program_date}'
        audiofile.tag.album_artist = program_performer
        audiofile.tag.recording_date = program_date
        audiofile.tag.original_release_date = program_date
        audiofile.tag.release_date = program_date
        audiofile.tag.tagging_date = program_date
        audiofile.tag.encoding_date = program_date
        audiofile.tag.track_num = 1

        audiofile.tag.save()
        
        return ''
    
    # Retrieve the final streaming URL
    def get_Stream_URL(self):
        stream_info = self.get_Stream_Info()
        auth_token = stream_info['token']
        chunk_url = stream_info['url']
        stream_url = f'{chunk_url}?X-Radiko-AuthToken={auth_token}'
        
        return stream_url
