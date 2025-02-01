#!/bin/bash
# https://ghfast.top/ # sleep 1
clun_download() {
cd ~ && curl -sS -o clun_tcp.sh https://raw.githubusercontent.com/cluntop/sh/main/tcp.sh && chmod +x clun_tcp.sh && ./clun_tcp.sh $1
} && clun_download
