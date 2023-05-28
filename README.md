# kisstvshow

https://kisstvshow.to/ scraper


## Install 
```sh
pip install kisstvshow
```


## Usage
```py
from kisstvshow import KissTVShow
import json

k = KissTVShow()
# show = k.get_show(show="Show/Outrun-by-Running-Man-2021")
# show = k.get_show_episode(show_ep="Show/Outrun-by-Running-Man-2021/Episode-14?id=29879")

show = k.search("hello")

print(json.dumps(show, indent=2))

```

## 
**&copy; 2023 | tbdsux**