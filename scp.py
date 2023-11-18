import re

# Implementation of the serial communication protocol

def reset() -> str:
    return f"r\n"

def get_version() -> str:
    return f"p\n"

def set_address(addr: str) -> str:
    return f"a[{addr}]\n"

def get_address() -> str:
    return f"a\n"

def configure(grp: int, par: int, val) -> str:
    return f"c[{grp},{par},{val}]\n"

def message(msg: str, dest: str) -> str:
    return f"m[{msg}\0,{dest}]\n"

def decode(data: str):
    # Possible formats
    # p[version]
    # a[addr]
    # c[grp, par, val]
    # m[T]
    # m[D]
    # m[R,type,message]
    # s[mode,type,src->dest,size(txsize),seq,cw,cwsize,dispatch,time]

    pattern = r'^[pacms]\[([^\]]*)\]$'
    match = re.match(pattern, data)
    return match.group(0), match.group(1).split(",")

