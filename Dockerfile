FROM golang:1.18 as builder

# install hln cli
WORKDIR /root/
RUN git clone https://github.com/h8r-dev/heighliner.git \
    && cd heighliner && make hln

FROM debian:bullseye-slim as downloader

RUN apt-get update   \
    && apt-get install -y curl unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install dagger
ENV DAGGER_VERSION 0.2.18
RUN cd /usr/local \
    && curl -L https://dl.dagger.io/dagger/install.sh | sh \
    && dagger version

# install terraform
ENV TF_VERSION 1.1.9
RUN ARCH= && dpkgArch="$(dpkg --print-architecture)" \
    && case "${dpkgArch##*-}" in \
    amd64) ARCH='amd64';; \
    arm64) ARCH='arm64';; \
    *) echo "unsupported architecture"; exit 1 ;; \
    esac \
    && curl -fsSLO --compressed "https://releases.hashicorp.com/terraform/$TF_VERSION/terraform_${TF_VERSION}_linux_$ARCH.zip" \
    && curl -fsSLO "https://releases.hashicorp.com/terraform/$TF_VERSION/terraform_${TF_VERSION}_SHA256SUMS" \
    && grep " terraform_${TF_VERSION}_linux_$ARCH.zip\$" "terraform_${TF_VERSION}_SHA256SUMS" | sha256sum -c - \
    && unzip -d /usr/local/bin "terraform_${TF_VERSION}_linux_$ARCH.zip" \
    && rm "terraform_${TF_VERSION}_linux_$ARCH.zip" "terraform_${TF_VERSION}_SHA256SUMS" \
    && terraform version

FROM debian:unstable-slim
RUN apt-get update && apt-get install ca-certificates -y

WORKDIR /root/

COPY --from=builder /root/heighliner/bin/hln /usr/local/bin/
COPY --from=downloader /usr/local/bin/dagger /root/.hln/bin/
COPY --from=downloader /usr/local/bin/terraform /root/.hln/bin/
