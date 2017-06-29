'''
JSON token scanner
'''

import re

__all__ = ['make_scanner']


'''
re.DOTALL: Make the '.' special character match any character at all,
including a newline; without this flag, '.' will match anything except a newline.

re.re.VERBOSE: This flag allows you to write regular expressions that look nicer and are more readable
like:
a = re.compile(r"""\d +  # the integral part
                   \.    # the decimal point
                   \d *  # some fractional digits""", re.X)
b = re.compile(r"\d+\.\d*")

and re.MULTILINE:
When specified, the pattern character '^' matches at the beginning
of the string and at the beginning of each line (immediately following each newline);
 and the pattern character '$' matches at the end of the string and at the end of each
 line (immediately preceding each newline)


 (?:pattern) doesn't capture match
'''
NUMBER_RE = re.compile(r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
                       (re.VERBOSE | re.MULTILINE | re.DOTALL))


def py_make_scanner(context):
    parse_object = context.parse_object
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    parse_float = context.parse_float
    parse_int = context.parse_int

    # parse_constant = context.parse_constant

    def _scan_once(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration

        # match string
        if nextchar == '"':
            return parse_string(string, idx + 1)
        # match object
        elif nextchar == '{':
            return parse_object((string, idx + 1), _scan_once)
        # match array
        elif nextchar == '[':
            return parse_array((string, idx + 1), _scan_once)
        # match null
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            return None, idx + 4
        # match true
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            return True, idx + 4
        # match false
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            return False, idx + 5

        # regex.match(string[, pos[, endpos]])
        # match the string from the pos position to endposition
        # mactch number
        m = match_number(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            # mactch float
            if frac or exp:
                res = parse_float(integer + (frac or '') + (exp or ''))
            # match integer
            else:
                res = parse_int(integer)
            # m.end() is the nextchar pos of end number
            return res, m.end()
        else:
            raise StopIteration
        '''
        elif nextchar == 'N' and string[idx:idx + 3] == 'NaN':
            return parse_constant('NaN'), idx + 3
        elif nextchar == 'I' and string[idx:idx + 9] == 'Infinity':
            return parse_constant('Infinity'), idx + 9
        '''

    return _scan_once


make_scanner = py_make_scanner
