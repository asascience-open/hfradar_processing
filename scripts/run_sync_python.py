import paramiko
import boto3
import sys
from io import StringIO
import logging

def sync_site(site: str):
    ssm = boto3.client("ssm")
    username, host, directory, password = [param_dict["Value"] for param_dict
                                    in (ssm.get_parameters(Names=[f"/hfradar/sprk/{param_name}"
                                    for param_name in ("SSH_USER", "SSH_HOST",
                                    "SSH_DIR", "SSHPASS")], WithDecryption=True)
                                    ["Parameters"][::-1])]
    # TODO: allow port customization
    transport = paramiko.Transport((host, 22))
    transport.connect(username=username, password=password)
    sftp = paramiko.sftp_client.SFTPClient.from_transport(transport)
    s3 = boto3.client("s3")
    # TODO: possibly add datetime limiter to avoid iterating over all files
    # if datetime format in filenames is consistently applied
    for subdirectory in ["MeasPattern", "IdealPattern"]:
        try:
            sftp_search_location = "{directory}/{subdirectory}"
            sftp.chdir(f"{directory}/{subdirectory}")
            sftp_file_names = set(sftp.listdir())
        # TODO: refine exception classes
        except:
            logging.exception(f"{sftp_search_location} failed to list files "
                              "for site {site}, possibly due to nonexistent directory")
            continue
        try:
            file_metadata_dict = {file_dict["Key"].rsplit("/")[-1]: file_dict for
                                  file_dict in s3.list_objects(Bucket="hfradar",
                                  Prefix=f"{site}/{subdirectory}/")["Contents"]}
        # if a subpath doesn't exist for the particular site, it will soon
        except:
            file_metadata_dict = {}
        for sftp_file_name in sftp_file_names:
            if sftp_file_name not in file_metadata_dict:
                fh = sftp.file(sftp_file_name)
                logging.info(f"Wrote {sftp_file_name} to S3")
                s3.put_object(Body=fh, Bucket="hfradar",
                              Key=f"{site}/{subdirectory}/{sftp_file_name}")

def main():
    sync_site(sys.argv[1])

if __name__ == "__main__":
    main()
