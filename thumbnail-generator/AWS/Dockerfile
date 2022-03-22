FROM mcr.microsoft.com/azure-cli:2.29.2

ENV TERRAFORM_VERSION=0.15.5

RUN apk update && \
    apk add curl jq python3 bash ca-certificates git openssl unzip wget && \
    cd /tmp && \
    wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/bin && \
    rm -rf /tmp/* && \
    rm -rf /var/cache/apk/* && \
    rm -rf /var/tmp/*