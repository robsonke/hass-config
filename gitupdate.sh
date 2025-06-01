#!/bin/bash
# add the ssh key to the agent
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_rsa -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'

git add .
git status

read -r -p "Enter the Description for the Change: " -i "Minor Updates" -e CHANGE_MSG

git commit -m "${CHANGE_MSG}"
git push origin master
exit
