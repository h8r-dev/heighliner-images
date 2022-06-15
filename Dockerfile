FROM debian:unstable-slim

RUN apt-get update   \
    && apt-get install -y curl   \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install hln cli
RUN curl -L https://dl.h8r.io/hln/install.sh | sh