import re
import sys
import logging
import io
import datetime
import urllib.parse
import boto3

s3 = boto3.client("s3")

def output_files(bucket: str, site: str, measurement_type: str, filename: str,
                 file_handle: io.TextIOWrapper):
    data_lines = []
    header_footer_lines = [], []
    is_footer = False
    for line in file_handle:
        # match headers
        if maybe_match_ts := re.match(r"(?<=%TimeStamp: )\d{4}, \d{2} \d{2}"
                                    r"  \d{2} \d{2} \d{2}",
                                    line):
            timestamp_str = maybe_match_ts.group(0)
        if maybe_match_tz := re.match(r'(?<TimeZone: [^"]+]', line):
            timezone_str = maybe_match_tz.group(0)
            timestamp_with_tz_string = str(datetime.strptime("%Y %m %d"
                                                          " %H %M %S %Z"))

        if not re.match(r"( |%%\s+(Longitude|\(deg\)))", line):
            header_footer_lines[is_footer].append(line)
        else:
            # switch to footer once returning back to comments, etc
            is_footer = True
            if not line.startswith("%%"):
                processed_line = re.sub("(?<![A-Z])\s+(?!$)", ",", line.strip()
                                        + "\n")
                data_lines.append(processed_line)
            else:
                processed_line = line
                data_lines.append(
                    f"{timestamp_with_tz_string},{processed_line}")
    file_name_base = filename
    # header lines can't reliably be parsed, use short names
    data_lines.insert(0,
                      "timestamp," +
                      header_footer_lines[0][-3][19:].strip().replace(" ", ",")
                      + "\n")
    base_path = f"{site}/{measurement_type}_processed/{filename}"

    # TODO: DRY up/ partial function application
    s3.put_object(Bucket=bucket, Key=f"{base_path}.header.txt",
              Body="".join(header_footer_lines[0]))
    s3.put_object(Bucket=bucket, Key=f"{base_path}.data_section.csv",
                  Body="".join(data_lines))
    s3.put_object(Bucket=bucket, Key=f"{base_path}.footer.txt",
                  Body="".join(header_footer_lines[1]))

def lambda_handler(event, context):
    # usually "hfradar" bucket
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'],
                                    encoding='utf-8')
    try:
        site, measurement_type, filename = key.split("/")
    except ValueError:
        print(f"Unable to split into site and type, key was f{key}.")
        logging.exception(f"Unable to split into site and type, key was f{key}.")
        raise
    # avoid looping on S3 file
    if measurement_type.endswith("processed"):
        return
    try:
        print(bucket, key)
        response = s3.get_object(Bucket=bucket, Key=key)
        contents = io.StringIO(response["Body"].read().decode("utf-8"))
        output_files(bucket, site, measurement_type, filename, contents)
    except:
        print("Exception occurred while attempting to fetch response from S3 "
              "object")
        logging.exception("Exception occurred while attempting to fetch "
                         "response from S3 object")
        raise
