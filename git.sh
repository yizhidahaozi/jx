#!/bin/bash

branch() {
   git pull origin main
}

submit() {
    git pull origin main && git add . && git status
    git commit -m "Update Up"
    git push origin HEAD:main
}

garbage() {
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive --prune
}

while true; do

echo -e "\n请选择要执行的操作"
echo "1. 提交更改"
echo "2. 远程分支"
echo "3. 远程分支"
echo "4. 查看状态"
echo "0. 退出菜单"

read -p "您的选项：" choice

case $choice in
    1) submit ;;
    2) branch ;;
    3) git status ;;
    4) garbage ;;
    0) echo -e "\n退出选项" ; exit 0 ;;
    *) echo -e "\n无效选项" ;;
    esac

    read -p $'\n返回菜单' -n 1 -r
    clear
done
