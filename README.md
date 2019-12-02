# Software Engineering(Team 00-zero)

## Info
[Our Website](http://augmentedmode.pythonanywhere.com/)

[Flask docs](http://exploreflask.com/en/latest/index.html)

[Flask tutorials](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## Setup
Depending on your system you may need to use py or python3 instead of python
Installation:
```
cd OOZero
pip install -r requirements.txt
python setup.py develop
or
python setup.py install
```
Download the 'config.cfg' file, place it in the OOZero directory and
set this environment variable (and replace your_flask_dir with the directory
of your local project):
```
OOZERO_CONFIG = your_flask_dir/OOZero/config.cfg
```
Running:
```
Windows Powershell: 
    $env:FLASK_APP = "flask_app"
    $env:OOZERO_CONFIG = "your_flask_dir/OOZero/config.cfg"
Windows CMD: 
    set FLASK_APP=flask_app
    set OOZERO_CONFIG=your_flask_dir/OOZero/config.cfg
Linux Bash: 
    export FLASK_APP=flask_app
    export OOZERO_CONFIG=your_flask_dir/OOZero/config.cfg

    python tests/generateDB.py

flask run
```
Generate development database with dummy data
```
python tests/generateDB.py
```
## Testing:

```
python setup.py test
or
pytest
```

## Maintance:
NEVER COMMIT THE CONTENTES OF ./instance/ to the repository. This directory contains the secret keys and other deployment spcific infomation. To obtain this directory please ask.


## Positions:
* President - Jacob Lebowitz
* Scrum Master - Luke
* Market Analyst - Chael
* Requirement Analyst - Rabah
* Developer - Jared
* Developer - Abbey
* Developer - Nick
* Developer - Jake
* Tester - Ryan K
* Tester - Ryan #2
* Operations Engineer - Kane
