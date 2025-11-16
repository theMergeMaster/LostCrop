# Lost Crop

Client-side terminal designed to manage your Minecraft servers


## What can you do

- Check the current status of the server
- Check how many players are connected and their names (WIP)
- Save, override, delete coords into a Google Sheets (WIP)
- Review all the commands you are allowed to use in a beautiful format (WIP)


## Dependencies
```
asyncio-dgram
cachetools
certifi
charset-normalizer
dnspython
google-auth
google-auth-oauthlib
gspread
idna
mcstatus
oauthlib
pyasn1
pyasn1-modules
requests
requests-oauthlib
rsa
setuptools
urllib3
```

### Adding dependencies
```sh
uv add httpx
```
or
```sh
uv add -r requirements.txt --active
```

### Lock dependencies
```sh
uv lock
```


## How to run locally
```sh
uv run lostcrop/main.py 
```