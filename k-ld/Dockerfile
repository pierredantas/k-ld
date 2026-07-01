# K-LD toolchain image: the K framework (v7.1.x) on Ubuntu Noble.
# amd64-only .deb, run under emulation on Apple Silicon (--platform linux/amd64).
# Doubles as the artifact-evaluation image for the paper.
FROM --platform=linux/amd64 ubuntu:24.04

ARG K_VERSION=7.1.337
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates make z3 \
 && curl -sSL -o /tmp/k.deb \
      "https://github.com/runtimeverification/k/releases/download/v${K_VERSION}/kframework_${K_VERSION}_amd64_ubuntu_noble.deb" \
 && apt-get install -y --no-install-recommends /tmp/k.deb \
 && rm -rf /tmp/k.deb /var/lib/apt/lists/*

WORKDIR /work
CMD ["bash"]
