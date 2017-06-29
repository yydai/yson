'''
Implementation of JSONDecoder
'''

import re
from yson import scanner

__all__ = ['JSONDecoder']

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL


def linecol(doc, pos):
    # get line number of current position
    lineno = doc.count('\n', 0, pos) + 1
    if lineno == 1:
        colno = pos + 1
    else:
        # get the column number of current position in current line
        colno = pos - doc.rindex('\n', 0, pos)

    return lineno, colno


WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'


# may have bugs
def pass_whitespace(s, idx):
    if (idx < len(s)) and (s[idx] in WHITESPACE_STR):
        idx += 1
        try:
            if s[idx] in WHITESPACE_STR:
                idx = WHITESPACE.match(s, idx).end()
        except IndexError:
            pass
    return idx


BACKSLASH = {
    '"': u'"', '\\': u'\\', '/': u'/',
    'b': u'\b', 'f': u'\f', 'n': u'\n', 'r': u'\r', 't': u'\t',
}

DEFAULT_ENCODING = 'utf-8'


def errmsg(msg, doc, pos, end=None):
    lineno, colno = linecol(doc, pos)
    if end is None:
        fmt = '{0}: line {1} column {2} (char {3})'
        return fmt.format(msg, lineno, colno, pos)
    endlineno, endcolno = linecol(doc, end)
    fmt = '{0}: line {1} column {2} - line {3} column {4} (char {5} - {6})'
    return fmt.format(msg, lineno, colno, endlineno, endcolno, pos, end)


def _decode_uXXXX(s, pos):
    esc = s[pos + 1:pos + 5]
    if len(esc) == 4 and esc[1] not in 'xX':
        try:
            # the 16 is base
            return int(esc, 16)
        except ValueError:
            pass

    msg = "Invalid \\uXXXX escape"
    raise ValueError(errmsg(msg))


def py_scanstring(s, idx, _b=BACKSLASH):
    # [\x00-\x1f] is Ascii control characters, below also include '"' and '\'
    # any unicode character except " or \ or control character
    STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)

    encoding = DEFAULT_ENCODING
    chunks = []
    _append = chunks.append
    begin = idx - 1

    while True:
        chunk = STRINGCHUNK.match(s, idx)
        if chunk is None:
            raise ValueError(
                errmsg('Unterminated string starting at', s, begin))

        idx = chunk.end()
        content, terminator = chunk.groups()
        if content:
            if not isinstance(content, unicode):
                content = unicode(content, encoding)
            _append(content)

        if terminator == '"':
            break

    return ''.join(chunks), idx


def JSONObject(s_and_idx, scan_once, memo=None, w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, idx = s_and_idx
    if memo is None:
        memo = {}
    # setdefault
    # If key is in the dictionary, return its value. If not,
    # insert key with a value of default and return default.
    # default defaults to None.

    while True:
        idx = pass_whitespace(s, idx)
        nextchar = s[idx]
        if nextchar == '"':
            res, idx = scan_once(s, idx)
        idx = pass_whitespace(s, idx)
        nextchar = s[idx]
        if nextchar != ':':
            raise ValueError(errmsg("Need ':' delimiter"))
        else:
            idx += 1
        idx = pass_whitespace(s, idx)
        try:
            value, idx = scan_once(s, idx)
        except StopIteration:
            raise ValueError(errmsg("Expecting object", s, idx))

        memo[res] = value
        idx = pass_whitespace(s, idx)
        nextchar = s[idx]

        idx += 1
        if nextchar == '}':
            break
        if nextchar != ',':
            raise ValueError(errmsg("Expecting ',' delimiter", s, idx - 1))

        idx = pass_whitespace(s, idx)
    return memo, idx


def JSONArray(s_and_idx, scan_once, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, idx = s_and_idx
    values = []
    idx = pass_whitespace(s, idx)
    nextchar = s[idx]
    if nextchar == ']':
        return values, idx + 1

    _append = values.append

    while True:
        try:
            value, idx = scan_once(s, idx)
        except StopIteration:
            raise ValueError(errmsg("Expecting object", s, idx))
        _append(value)
        idx = pass_whitespace(s, idx)
        nextchar = s[idx:idx + 1]

        idx += 1
        if nextchar == ']':
            break
        if nextchar != ',':
            raise ValueError(errmsg("Expecting ',' delimiter", s, idx - 1))

        idx = pass_whitespace(s, idx)

    return values, idx


class JSONDecoder(object):
    '''
    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | unicode           |
    +---------------+-------------------+
    | number (int)  | int, long         |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+

    '''

    def __init__(self):
        self.parse_int = int
        self.parse_float = float
        self.parse_object = JSONObject
        self.parse_array = JSONArray
        self.parse_string = py_scanstring
        self.scan_once = scanner.make_scanner(self)

    def decode(self, s, _w=WHITESPACE.match):
        # start from nonspace char
        obj, end = self.raw_decode(s, idx=_w(s, 0).end())
        end = _w(s, end).end()
        if end != len(s):
            raise ValueError(errmsg("Extra data", s, end, len(s)))
        return obj

    def raw_decode(self, s, idx=0):
        try:
            obj, end = self.scan_once(s, idx)
        except StopIteration:
            raise ValueError("No JSON object could be decoded")
        return obj, end


if __name__ == '__main__':
    j = JSONDecoder()
    a = j.decode('[12, 23, 45.3, "hello world", {"aaa": 123}]')
    b = '''{
    "name": "dai ying",
    "age" : 20,
    "family": {
    "father": "Dai Hongjun",
    "mother": "zhenbenying"
    },
    "hobby": ["game", "guitar", "Emacs"]}
    '''
    b = j.decode(b)
    print type(a)
    print a
    print type(b)
    print b
