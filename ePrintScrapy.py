from ePrint import ePrint_payload, ePrint_download
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-j", "--jobs", help="parallel jobs, default=6", type=int, default=6)
parser.add_argument("-p", "--payload", default="payload.json", help="payload json file, default=payload.json")
parser.add_argument("target_dir", help="target dir")
args = parser.parse_args()

payload = json.load(open(args.payload, 'r'))
ePrint_download(args.target_dir, ePrint_payload(**payload), args.jobs)
