#! /bin/bash
#Builds weresync into python .whl packages

WERESYNC_V=$1

. bin/activate

python setup.py sdist bdist_wheel bdist_egg
twine upload -s -i dmv@springwater7.org dist/WereSync-$WERESYNC_V-py3-none-any.whl dist/WereSync-$WERESYNC_V.tar.gz dist/WereSync-$WERESYNC_V-py3.4.egg

cd docs
make html

cd ..
python setup.py upload_docs

