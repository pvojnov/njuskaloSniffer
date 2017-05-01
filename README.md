"# njuskaloSniffer"

## Install
...x-sh
$ pip install virtualenv
$ pip install virtualenvwrapper
$ export WORKON_HOME=~/Envs
$ source /usr/local/bin/virtualenvwrapper.sh

$ apt-get install libxml2-dev libxslt-dev python-dev
$ apt-get build-dep python3-lxml
$ apt-get install language-pack-hr
$ dpkg-reconfigure locales
$ apt-get install libgeos-dev


$ pip install -r requirements.txt
...

## Run setup

...x-sh
$ mkvirtualenv njuskalo_sniffer
& mkdir njuskalo_sniffer
...




## Run command
...x-sh
$ workon njuskalo_sniffer
$ cd ~/njuskalo_sniffer/njuskalo_kuce/recentDownload
$ python emailInterestingAdds.py
...