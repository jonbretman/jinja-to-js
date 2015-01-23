#!/bin/bash

set -e
set -x

# add mega-python ppa
sudo add-apt-repository -y ppa:fkrull/deadsnakes
sudo apt-get -y update

# install node
sudo add-apt-repository -y ppa:chris-lea/node.js
sudo apt-get -y update
sudo apt-get install -y nodejs

case "${TOX_ENV}" in
    py26)
        sudo apt-get install python2.6 python2.6-dev
        ;;
    py33)
        sudo apt-get install python3.3 python3.3-dev
        ;;
    py34)
        sudo apt-get install python3.4 python3.4-dev
        ;;
    py3pep8)
        sudo apt-get install python3.3 python3.3-dev
        ;;
    pypy)
        sudo add-apt-repository -y ppa:pypy/ppa
        sudo apt-get -y update
        sudo apt-get install -y --force-yes pypy pypy-dev
        ;;
esac

sudo pip install virtualenv

virtualenv ~/.venv
source ~/.venv/bin/activate
pip install tox
