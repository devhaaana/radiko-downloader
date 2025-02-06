import time
import argparse
import warnings
warnings.filterwarnings(action='ignore')

from radiko_urllib3 import *
from utils import *


def setting_argument():
    parser = argparse.ArgumentParser(description="Radiko Stream Recorder")
    
    parser.add_argument('--version', type=str, default='1.0.0', help='Version of the application')
    parser.add_argument('--station', type=str, default='TBS', help='Stream Station ID (e.g., TBS, LFR)')
    parser.add_argument('--areaFree', type=str2bool, default=False, help='Whether the stream is area-free')
    parser.add_argument('--timeFree', type=str2bool, default=False, help='Whether the stream is time-free')
    parser.add_argument('--startTime', type=str, default=None, help='Stream start time (format: YYYYMMDDHHMM)')
    parser.add_argument('--endTime', type=str, default=None, help='Stream end time (format: YYYYMMDDHHMM)')
    parser.add_argument('--save', type=str2bool, default=False, help='Whether to save the stream as a file')
    parser.add_argument('--output_dir', type=str, default='./data', help='Directory to save output files')
    
    args = parser.parse_args()
    
    return args


def main():
    args = setting_argument()
    
    radiko = Radiko(args)
    start_time = time.time()
    
    if args.save == True:
        stream = radiko.save_program()
        
    print(f"Execution Time: {time.time() - start_time:.4f} sec")
 
 
if __name__ == '__main__':
    main()
