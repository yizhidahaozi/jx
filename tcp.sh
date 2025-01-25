#!/bin/bash
clun_download() {
cd ~ && sleep 1 && curl -sS -o clun_tcp.sh https://fastly.jsdelivr.net/gh/cluntop/sh@main/tcp.sh && chmod +x clun_tcp.sh && ./clun_tcp.sh
} && clun_download
