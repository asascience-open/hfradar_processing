#!/usr/bin/env sh
set -eu

# SITE env var is expected to be set, it determines which parameters/secrets
# to pull

# TODO: mount as RO volume instead? Currently unused until mechanism determined
# for public/private key setting
#umask 077
#if [ -n "$SSH_PUB_KEY" ]; then
#    # assuming RSA here, is there a generic filename that can be used?
#    echo "$SSH_PUB_KEY" > ~/.ssh/id_rsa.pub
#fi
#if [ -n "$SSH_PRIV_KEY" ]; then
#    echo "$SSH_PRIV_KEY" > ~/.ssh/id_rsa
#fi
SSH_HOST="$(aws ssm get-parameter --name "/hfradar/$SITE/SSH_HOST" --region us-east-1 | jq -r .Parameter.Value)"
SSH_USER="$(aws ssm get-parameter --name "/hfradar/$SITE/SSH_USER" --region us-east-1 | jq -r .Parameter.Value)"
SSH_DIR="$(aws ssm get-parameter --name "/hfradar/$SITE/SSH_DIR" --region us-east-1 | jq -r .Parameter.Value)"
# TODO: some hosts might not use SSH password, e.g. public/priv key pair
#       handle these appropriately
SSHPASS="$(aws ssm get-parameter --with-decryption --name "/hfradar/$SITE/SSHPASS" --region us-east-1 | jq -r .Parameter.Value)"

# should never be mounted in ephemeral container case
if ! mountpoint -q /mnt/ssh_mount; then
    if [ -n "$SSHPASS" ]; then
        echo "$SSHPASS" | sshfs -o 'StrictHostKeyChecking=no' -o password_stdin \
                             "$SSH_USER@$SSH_HOST:$SSH_DIR" /mnt/ssh_mount
    else
        sshfs -o 'StrictHostKeyChecking=no' "$SSH_USER@$SSH_HOST:$SSH_DIR" \
                                              /mnt/ssh_mount
    fi
fi 

aws s3 sync --storage-class GLACIER /mnt/ssh_mount \
                                    "s3://hfradar/$SITE"
