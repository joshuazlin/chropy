"""
General utility functions
"""

import re

def finv(x,pattern):
    """
    Inverse f-string function. For example, an f-string might be
      f'_{a}_{b}_' = '_apple_banana_'
    To invert it, we can run

    >>> finv('_apple_banana_','_{a}_{b}_')
    {'a': 'apple', 'b': 'banana'}

    finv will try and make the matched groups go as far to the right as possible
    >>> finv("yxxy","{a}x{b}")
    {'a': 'yx', 'b': 'y'}

    You don't need to 'match onto the whole string', and groups will fill up as much as possible
    >>> finv("yxy","{a}x")
    {'a': 'y'}

    Typical use-case
    >>> finv("prop_2+1f_24nt64_IWASAKI_b2.13_ls16_M1.8_ms0.04_mu0.005_mv0.005_srcx8y8z8t5.975","ms{ms}_mu{mu}_mv{mv}_srcx{x}y{y}z{z}t{t}.{cfg}")
    {'ms': '0.04', 'mu': '0.005', 'mv': '0.005', 'x': '8', 'y': '8', 'z': '8', 't': '5', 'cfg': '975'}
    """
    #Make sure that the special characters are escaped properly
    a0 = re.sub('\.','\\.',pattern)
    a1 = re.sub('\_','\\_',a0)
    a2 = re.sub('\{','(?P<',a1)
    a3 = re.sub('\}','>.*)',a2)
    return re.search(a3,x).groupdict()
    
def split_list(l,n):
    """
    Split list l into n components

    >>> split_list(list(range(5)),1)
    [[0, 1, 2, 3, 4]]
    >>> split_list(list(range(5)),2)
    [[0, 1], [2, 3, 4]]
    >>> split_list(list(range(5)),5)
    [[0], [1], [2], [3], [4]]
    >>> split_list(list(range(5)),6)
    Traceback (most recent call last):
    Exception: Length of list 5 should not exceed number of sublists requested 6
    """
    a = len(l)//n
    if a == 0:
        raise Exception(f'Length of list {len(l)} should not exceed number of sublists requested {n}')
    to_return = []
    for i in range(n):
        if i == n-1:
            to_return.append(l[i*a:])
        else:
            to_return.append(l[i*a:(i+1)*a])
    return to_return
                      
def dict_intersect(d1,d2):
    """
    Intersect two dictionaries...(?)
    """
    d = {}
    for k in d1.keys():
        if k not in d2.keys():
            continue
        x = list(set(d1[k]).intersection(set(d2[k])))
        if len(x) > 0:
            d[k] = x
    return d 
        

