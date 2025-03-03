#!/bin/bash
clun_download() {
cd ~ && curl -sS  gh.clun.top/github.com/cluntop/sh/raw/refs/heads/main/tcp.sh -o clun_tcp.sh && chmod +x clun_tcp.sh && ./clun_tcp.sh $1
} && clun_download $1
