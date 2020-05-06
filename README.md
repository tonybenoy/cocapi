<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/Tests/badge.svg" alt="Test Status" height="15">
    </a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python version" height="15"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/master/LICENSE"><img src="https://img.shields.io/pypi/l/markdown-subtemplate.svg" alt="License" height="15"></a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Codestyle Black" height="15">
    </a>
</p>
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
*Note versions below 2.0.0 are not supported anymore*