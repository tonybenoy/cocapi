# ClashOfClansAPI </br>
Python Wrapper for SuperCells Clash Of Clans API </br>
Get Token from https://developer.clashofclans.com/</br>


# Install using pip </br>

> pip3 install cocapi


# Usage </br>

```
from cocapi import CocApi
token = 'YOUR_API_TOKEN';
timeout=1 #requests timeout 
api=CocApi(token,timeout)
api.clan_members("#PU8J2RQ")
```
