_hexdig = '0123456789ABCDEFabcdef'
_hextobyte = None

def unquote(string):
    """
    @brief Remove URL encoding from a string, i.e.
           unquote('abc%20def') -> 'abc def', see
           urllib.parse.unquote_to_bytes()
    @param string String that might contain URL/percent encoding
    @return string with URL encoding replaced by original characters
    """
    global _hextobyte

    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        return ""

    if isinstance(string, str):
        string = string.encode('utf-8')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string.decode('utf-8')

    res = [bits[0]]
    append = res.append

    # Delay the initialization of the table to not waste memory
    # if the function is never called
    if _hextobyte is None:
        _hextobyte = {(a + b).encode(): bytes([int(a + b, 16)])
                      for a in _hexdig for b in _hexdig}

    for item in bits[1:]:
        try:
            append(_hextobyte[item[:2]])
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)

    return (b''.join(res)).decode('utf-8')
