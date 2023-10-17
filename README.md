# hfradar_processing
Processing scripts for HF Radar

## Scripts

Run `SITE=<site> run_sync.sh`.  `SITE` should be a site in HF Radar in the AWS System Manager Parameter Store.

## General workflow

![image](https://github.com/asascience-open/hfradar_processing/assets/4118886/bfcc25b7-e1af-4921-9237-e44952fa4c9a)


Files are synced over to AWS S3 via SSH through AWS Lambda containers.  Event listeners detect when a file has been written and split files into header, footer, and data sections.  ERDDAP then reads these data sections to serve up the contents of the files.
