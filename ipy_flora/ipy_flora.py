#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
IPython extension for XSB / Flora2 / ReasonablePy / rpsimple

…extends your python-shell by Logic-programming
…a better read-evaluation-print-loop for Flora2 instead of runflora

Features and Usage:

* You will find an rpsimple-instance at: 
  [IPython]> IP.flora_instance
* Example (more complicated than needed, but how flora-users know it):
  [IPython]> cmd = "writeln(''hello world'')@_prolog."
  [IPython]> IP.flora_instance.query(cmd)
* For Help how to use this inspect rpsimple:
  [IPython]> IP.flora_instance ??

* Magic-shortcuts help to use it more efficient
  [IPython]> ++ life:Thing
  [IPython]> ++ universe:Thing
  [IPython]> ++ Thing::Everything
  [IPython]> ++ Everything[answer*->?X] :- ?X is 6*7
  [IPython]> ++ "answer to life, the universe and everything"(?X) :- life[answer->?X], universe[answer->?X], Everything[answer*->?X
  [IPython]> ?- "answer to life, the universe and everything"( ?TheAnswer )     // You know the result ;)

* For list of all available shortcuts see:
  [IPython]> import ipy_flora
  [IPython]> ipy_flora.init_ipython ??
* For help about flora read flora2.pdf

* Sophisticated tab-completion :)
* Simply try, for details inspect:
  [IPython]> import ipy_flora
  [IPython]> ipy_flora.completer_flora ??

* A mechanism to inspect your flora-instance
  printing occurrences of identifiers in knowledge-base
  (from currently loaded facts&rules or from original file)
* It is invoked when pressing <TAB> when cursor is over an identifier
  and line ends with „?“ or „??“
* „?“ yield all matching definitions
* „??“ yields all occurrences
* For details see implementation:
  [IPython]> import ipy_flora
  [IPython]> ipy_flora.completer_flora ??

* a more complex example can be found in ./test_and_tutorial.py
"""

is_identifier = lambda char: (char.isalnum() or char in ['_'])
brackets = [('{', '}'), ('(', ')'), ('[', ']')]
brackets_counter = lambda string: sum([string.count(br_open) - string.count(br_close) for(br_open, br_close) in brackets])


def do_flora_auto(self, arg):
    """Auto-Parse and run Flora-Commands"""
    return self.flora_instance.auto(arg, verbose=True)

def do_flora_query(self, arg):
    """Run Flora-Query"""
    return self.flora_instance.query_advanced(arg, verbose=True)

def do_flora_insert(self, arg):
    """Insert Flora-Fact/Rule"""
    self.flora_instance.modifykb(arg, 'insert', verbose=True)

def do_flora_delete(self, arg):
    """Insert Flora-Fact/Rule"""
    self.flora_instance.modifykb(arg, 'delete_auto', verbose=True)

def do_flora_abolish_all_tables(self, arg):
    """Clear tabling-cache"""
    self.flora_instance.query('abolish_all_tables.')

def do_flora_pprint(self, arg):
    """prettyprint flora-object"""
    self.flora_instance.query('[prettyprint>>pp].')
    self.flora_instance.query(arg + '[%pp_self]@pp.')

def do_flora_save(self, arg):
    """save main-module to file"""
    assert len(arg.split()) == 1, 'Expects exactly one argument: filename'
    self.flora_instance.query('_save(' + arg + ').')
    from rpsimple import format_flr
    return format_flr(arg + '.flr', writeback=True)

def do_flora_completer_update(self, arg):
    """Update the tab-completer — load a file with known tokens / compound functions"""
    from rpsimple import format_flr
    if hasattr(self, 'flora_completer_file'):
        self.flora_completer_listing = open(self.flora_completer_file, 'r').readlines()
    else:
        self.flora_instance.query('_save(completion).')
        self.flora_completer_listing = format_flr('completion.flr', writeback=False)
        import os
        os.remove('completion.flr')
    return self.flora_completer_listing

def _getsymbols_(event_line, event_symbol):
    """parse line backward to find „symbol“
    (in opposite to event.symbol we want to be able to find symbol,
    when being after closing brackets of compound function.
    Different nested symbols can be found…
    >>> _getsymbols_('abc(d', 'd')
    ['d', 'abc(d']
    >>> _getsymbols_('abc(d), ef(g', 'g')
    ['g', 'ef(g']
    >>> _getsymbols_('abc(d), ef(g', 'ef')
    ['ef']
    >>> _getsymbols_('abc(d), ef(g', 'd')
    ['d', 'abc(d']
    """
    symbols = []
    inputstr = event_line[:event_line.rfind(event_symbol) + len(event_symbol)]
    while inputstr.endswith('?'):
        inputstr = inputstr[:-1]
    reverselist = list(inputstr.strip())
    reverselist.reverse()

    if len(reverselist) > 0:
        symbol = reverselist[0]
        open_brackets = brackets_counter(reverselist[0])
        for char in reverselist[1:]:
            #print (char, open_brackets)
            if open_brackets == 0 and not is_identifier(char):
                symbols.append(symbol)
                open_brackets -= 1  # now get symbol of next hierarchy
            open_brackets += brackets_counter(char)
            symbol = char + symbol
        if open_brackets == 0:
            symbols.append(symbol)
    return symbols

def _printhelp_(self, event_line, symbols):
    """Print Help about symbol
    ? -> All rules with symbol as start of head
    ?? -> All rules containing symbol

    >>> IP.flora_completer_listing = ['abc(de(f),?A) :- gh(?A).', 'abc(de(?A)) :- (de(g), abc(?A)).']
    >>> _printhelp_(IP, '?- d??', ['d', 'abc(d'])
    <BLANKLINE>
    1:   abc(de(f),?A) :- gh(?A).
    <BLANKLINE>
    2:   abc(de(?A)) :- (de(g), abc(?A)).
    >>> del IP.flora_completer_listing
    """
    if event_line.endswith('?'):
        continue_incomplete_line = False
        begin_of_cmd = ''
        linenr = 0
        for line in self.flora_completer_listing:
            linenr += 1
            line = line.replace('\n', '')
            pure_line = line.split('//')[0].split('/*')[0].strip()
            line_out = (str(linenr) + ':').ljust(5) + line
            for symbol in symbols:
                if (event_line.endswith('??') and line.find(symbol) != -1) \
                or (pure_line.startswith(symbol) and begin_of_cmd == '') \
                or continue_incomplete_line:
                    if not continue_incomplete_line:
                        print '\n' + begin_of_cmd + line_out
                    else:
                        print line_out
                    continue_incomplete_line = not pure_line.endswith('.')
                    break 
                else:
                    if line.strip() != '' and not pure_line.endswith('.'):
                        begin_of_cmd += line_out + '\n'
                    else:
                        begin_of_cmd = ''

def _parseEnd_(match):
    """Find the end of first compound in match
    We assume that only end is searched (result is prefix of argument)
    >>> _parseEnd_('a(b,c(?X)) :- d(?X)')
    'a(b,c(?X))'
    """

    """find end of identifier"""
    for idx in range(len(match)):
        if not is_identifier(match[idx]):
            break

    """find where all open brackets are closed"""
    open_brackets = brackets_counter(match[idx])
    idx += 1
    while open_brackets != 0:
        open_brackets += brackets_counter(match[idx])
        idx += 1

    result = match[:idx]
    if not is_identifier(result[-1]) and brackets_counter(result[-1]) == 0:
        return result[:-1]
    return result

def completer_flora(self, event, debug=False):
    """Tab-Completion for flora
    >>> IP.flora_instance.auto('++ abc(de(f), ?A) :- gh(?A)')
    >>> event = IPython.ipstruct.Struct({'line': '', 'symbol':''})
    >>> completer_flora(IP, event, debug=True)
    []
    >>> event = IPython.ipstruct.Struct({'line': 'abc(d', 'symbol':'d'})
    >>> completer_flora(IP, event, debug=True)
    ['de(f)', 'abc(de(f),?A)']

    ### Add a new fact and ask the same again ###
    >>> IP.flora_instance.auto('++ abc(de(?A)) :- de(g), abc(?A)')
    >>> event = IPython.ipstruct.Struct({'line': 'abc(d', 'symbol':'d'})
    >>> completer_flora(IP, event, debug=True)
    ['de(f)', 'abc(de(f),?A)']

    ### Nothing changed, since we did not update — but now… ###
    >>> do_flora_completer_update(IP, '')
    ['abc(de(f),?A) :- gh(?A).', 'abc(de(?A)) :- (de(g), abc(?A)).']
    >>> completer_flora(IP, event, debug=True)
    ['de(f)', 'de(?A)', 'de(g)', 'abc(de(f),?A)', 'abc(de(?A))']

    ### Use the help ###
    >>> event = IPython.ipstruct.Struct({'line': 'z(gh??', 'symbol':'gh'})
    >>> completer_flora(IP, event, debug=True)
    <BLANKLINE>
    1:   abc(de(f),?A) :- gh(?A).
    ['gh(?A)']
    """

    if event.line.endswith('!!') or not hasattr(self, 'flora_completer_listing'):
        self.magic_flora_completer_update(None)

    symbols = _getsymbols_(event.line, event.symbol)

    _printhelp_(self, event.line, symbols)

    """do the completion"""
    result = []
    if not debug:
        result += self.Completer.python_matches(event.symbol)  # regular py-completer

    known_content = ' '.join([l.strip() for l in self.flora_completer_listing])
    for symbol in symbols:
        idx = -1
        while True:
            idx = known_content.find(symbol, idx+1)
            if idx == -1:
                break
            if idx != 0 and is_identifier(known_content[idx-1]):
                #we don't want broken parts of identifiers
                continue
            match = known_content[idx:].strip()
            result += [_parseEnd_(match)]
    return result

def init_ipython(ip):
    """Initialize the Extension when IPython is loaded"""
    import rpsimple
    ip.IP.flora_instance = rpsimple.Flora2()

    ip.expose_magic('flora', do_flora_auto)
    ip.expose_magic('?-', do_flora_query)
    ip.expose_magic('++', do_flora_insert)
    ip.expose_magic('--', do_flora_delete)
    ip.expose_magic('flora_abolish_all_tables', do_flora_abolish_all_tables)
    ip.expose_magic('flora_pprint', do_flora_pprint)
    ip.expose_magic('flora_save', do_flora_save)
    ip.expose_magic('flora_completer_update', do_flora_completer_update)
    ip.set_hook('complete_command', completer_flora, re_key = '^(?!%flora[^ ]*$).*flora.*')
    ip.set_hook('complete_command', completer_flora, re_key = '^(\?-|\+\+|--).*')


if __name__ == '__main__':

    import IPython
    ipy = IPython.Shell.IPShellEmbed(user_ns=locals())
    IP = ipy.IP
    if not hasattr(IP, 'flora_instance'):
        print '\nYou should load „ipy_flora“ from your IPython-config — see INSTALL\n'
        IP.api.load('ipy_flora.ipy_flora')

    import doctest, sys
    result = doctest.testmod(extraglobs=locals())
    print result
    sys.exit(result.failed)
