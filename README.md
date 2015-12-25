# matascii

![](https://i.gyazo.com/8f02fc6f267c2f0d2e9a15e05f071d5b.png)

ASCII back-end for matplotlib

## Installation
```
git clone https://github.com/domitry/matascii.git
cd matascii
python setup.py
```

## How to use
```python
from matplotlib import pylab
import matascii
pylab.switch_backend("module://matascii")

# some lines here

pylab.show()
# or pylab.savefig("hoge.txt")
```
