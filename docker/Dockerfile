FROM alpine:3.18.3

RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache fuse sshfs sshpass aws-cli jq && \
    mkdir /mnt/ssh_mount /root/.ssh && chmod 700 /root/.ssh

COPY ./run_sync.sh /

CMD /run_sync.sh
