FROM python:3.10.5-alpine3.16

WORKDIR /root/

# Install ssh, curl
RUN apk update \
      && apk add --no-cache \
      openssh-client-default \
      curl gcc linux-headers musl-dev \
      libffi-dev

# Install k3sup
RUN curl -sLS https://get.k3sup.dev | sh

# Install dependencies.
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# Add all files.
COPY . .

# Remove build tools
RUN apk del gcc linux-headers musl-dev libffi-dev

CMD ["/bin/sh", "init-k8s.sh"]
