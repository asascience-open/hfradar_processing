# hfradar_processing
Processing scripts for HF Radar

## Scripts

Run `SITE=<site> run_sync.sh`.  `SITE` should be a site in HF Radar in the AWS System Manager Parameter Store.

## General workflow

![1d25c0c2-4de7-41f8-8f59-46069c913066](https://github.com/asascience-open/hfradar_processing/assets/4118886/d0e979fe-308d-4b46-b064-24a24bd928eb)

Files are synced over to AWS S3 via SSHFS mounts.  Event listeners detect when a file has been written and split files into header, footer, and data sections.  ERDDAP then reads these data sections to serve up the contents of the files.
