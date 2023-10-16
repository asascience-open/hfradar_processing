import asyncio
import aioboto3
import asyncssh
import logging
import sys

async def async_sync_site(site: str):
    session = aioboto3.Session()
    async with session.client("ssm", region_name="us-east-1") as ssm:
        ssm_params = await ssm.get_parameters(Names=[f"/hfradar/sprk/{param_name}" for param_name in ("SSH_USER", "SSH_HOST", "SSH_DIR", "SSHPASS")], WithDecryption=True)
        username, host, directory, password = [param["Value"] for param in ssm_params["Parameters"][::-1]]
    # TODO: how to close session?
    del session

    async with asyncssh.connect(host, username=username, password=password,
                                known_hosts=None) as conn:  # TOFU for now
        async with conn.start_sftp_client() as sftp:

            for subdirectory in ["MeasPattern", "IdealPattern"]:
                try:
                    sftp_search_location = f"{directory}/{subdirectory}"
                    await sftp.chdir(f"{directory}/{subdirectory}")
                    sftp_file_names = set(await sftp.listdir())
                except (OSError, asyncssh.SFTPError) as e:
                    logging.exception(f"{sftp_search_location} failed to list files for site {site}, possibly due to nonexistent directory")
                    continue

                session = aioboto3.Session()
                async with session.resource("s3") as s3:
                    bucket = await s3.Bucket("hfradar")
                    prefix = f"{site}/{subdirectory}/"

                    file_metadata_dict = {obj.key.rsplit("/")[-1]: obj async for obj in
                                          bucket.objects.filter(Prefix=prefix)}

                    async def maybe_write_to_s3(sftp_file_name):
                      # TODO: refine logic to handle datasets which might
                      # already exist but have different mtime or size
                      if (sftp_file_name not in file_metadata_dict and
                          sftp_file_name.endswith(".ruv")):
                         try:
                             async with sftp.open(sftp_file_name) as fh:
                                body_contents = await fh.read()
                                await bucket.put_object(Key=f"{prefix}{sftp_file_name}", Body=body_contents)
                                print(f"Wrote {sftp_file_name} to HF Radar S3 location {prefix}{sftp_file_name}")
                         except:
                             logging.exception(f"Exception occurred while trying to transfer file {sftp_file_name} to S3: ")

                    await asyncio.gather(*(maybe_write_to_s3(sftp_file_name) for sftp_file_name in
                                           sftp_file_names))

def main():
    asyncio.run(async_sync_site(sys.argv[1]))

if __name__ == "__main__":
    main()
