# ClashOfClansAPI </br>
Python Wrapper for SuperCells Clash Of Clan API </br>
Get Token from https://developer.clashofclans.com/</br>
#Usage </br>```
from cocapi import cocapi
token = 'YOUR_API_TOKEN';
timeout=1 #requests timeout 
api=cocapi(token,timeout)
api.clan_members("#PU8J2RQ")
```
