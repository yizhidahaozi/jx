#!/bin/bash
clun_download() {
cd ~ && curl -sS -o clun_tcp.sh https://gh.clun.top/github.com/cluntop/sh/raw/refs/heads/main/tcp.sh && chmod +x clun_tcp.sh && ./clun_tcp.sh $1
} && clun_download $1
# https://ghfast.top/ # sleep 1
