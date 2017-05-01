#!/bin/bash

export WORKON_HOME=~/Envs
source /usr/local/bin/virtualenvwrapper.sh
workon njuskalo_sniffer
cd ~/njuskalo_sniffer/njuskalo_kuce/recentDownload
python emailInterestingAdds.py