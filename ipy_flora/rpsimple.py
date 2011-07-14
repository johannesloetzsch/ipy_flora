#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
simpler interface to Flora2:

>>> f = Flora2()
>>> f.auto('p(23)', verbose=True, vverbose=True)
[insert{p(23)}.]
>>> f.auto('q(42).', verbose=True)
[insert]
>>> f.auto('q(?X) :- p(?X)', verbose=True)
[insertrule]
>>> f.auto('?- q(?Y)', verbose=True)
[refresh: q(?Y)]
[query for ['Y']]
['23', '42']
"""

import doctest
import rp
import re
import itertools
import sys

class Flora2(rp.interface.Flora2):

    def query(self, expr, varlist=[]):
        """default empty varlist"""
        return rp.interface.Flora2.query(self, expr, varlist)

    def query_advanced(self, expr, varlist=None, verbose=False, formatResult=True):
        """advanced version of query"""

        """complete and test expression"""
        expr = self._uncomment_(expr)
        expr += '.'

        assert re.match('^[^{]*:-[^}]*$', expr) == None, '„:-“ only within allowed „{ }“ allowed'

        """calculate varlist"""
        if varlist == None:
            varlist = []
            for match in re.finditer('\?(?P<var>[A-Z][a-zA-Z1-9_]*)', expr):
                var = match.groupdict()['var']
                assert '_' not in var, '„_“ is in Variables only allowed in first possition'
                varlist.append(var)
                varlist = list(set(varlist))


        """refresh (against problems with tabling)"""
        unrefreshable_expr = (True in [test in expr for test in ['{', '}', '@', '\\', '<']]) or \
                             re.match('.*[^-]>.*', expr) != None or \
                             re.match('.*:=:.*', expr) != None or \
                             re.match('.*not .*', expr) != None
        if unrefreshable_expr:
            """this case could be improved in future: parse the compound and refresh all it's parts"""
            if verbose:
                print '[unrefreshable]'
        else:
            if verbose:
                print '[refresh: ' + expr[:-1] + ']'
            self.query('refresh{' + expr[:-1] + '}.')
        if verbose:
            print '[query for ' + str(varlist) + ']'
        result =  self.query(expr, varlist)

        if not formatResult:
            """a stable format"""
            return (result, varlist)
        return self.format_result(result, varlist)

    def format_result(self, result, varlist):
        """returns Boolean, List or ListOfDict depending on number of vars"""
        if varlist == []:
            if result == [{}]:
                return True
            elif result == []:
                return False
            assert False, 'unexpected result'
        elif len(varlist) == 1:
            var = varlist[0]
            result = sorted(result)
            return [k[var] for k,v in itertools.groupby(result)]
        else:
            result = sorted(result)
            return [k for k,v in itertools.groupby(result)]

    def modifykb(self, expr, action=None, verbose=False, vverbose=False):
        """modify the knowledge-base (insert|delete[all])(fact|rule)"""

        """complete expression"""
        expr = self._uncomment_(expr)

        """calc clause-type"""
        if re.match('.*:-.*', expr) != None:
            clause_type = 'rule'
        else:
            clause_type = ''  # fact

        """calc action"""
        if action == None:
            if len(expr) >= 2 and expr[:2] == '--':
                expr = expr[2:]
                action = 'delete_auto'
            else:
                if len(expr) >= 2 and expr[:2] == '++':
                    expr = expr[2:]
                action = 'insert'

        if action == 'delete_auto':
            if clause_type == 'rule':
                action = 'delete'
            else:
                action = 'deleteall'

        assert action in [None, 'insert', 'delete', 'deleteall'], 'Action not allowed'

        """do it"""
        cmd = action + clause_type + '{' + expr + '}.'
        if verbose:
            if vverbose:
                print '[' + cmd + ']'
            else:
                print '[' + action + clause_type + ']'
        self.query(cmd, [])

    def auto(self, expr, **kwargs):
        """query or modifykb depending on parsing result"""
        expr = expr.strip()

        if expr[:2] == '?-':
            return self.query_advanced(expr[2:], **kwargs)
        else:
            return self.modifykb(expr, **kwargs)

    def _uncomment_(self, expr):
        """remove comments"""
        c_o = '//.*'
        expr = re.sub(c_o, '', expr)

        c_o = '/[*]'                # /*
        c_i = '([^*]|[*][^/])*'     # not */
        c_c = '[*]/'                # */
        (expr, count) = re.subn(c_o + c_i + c_c, '', expr)

        """remove final-marker „.“ (we add it later where correct)"""
        expr = re.sub('\.[ ]*$', '', expr)

        return expr.strip()


class InsecureVariable(TypeError):
    """Exception"""

def testVarSecurity(var, raiseE=True):
    """Test if var is save as argument for embedding into flora-query (prevent injections)
    >>> testVarSecurity('', raiseE=False)
    True
    >>> testVarSecurity(':-(', raiseE=False)
    False
    >>> testVarSecurity([''], raiseE=False)
    True
    >>> testVarSecurity(['', ''], raiseE=False)
    True
    >>> testVarSecurity([':-('], raiseE=False)
    False
    >>> testVarSecurity({0: ''}, raiseE=False)
    True
    >>> testVarSecurity({0: ':-('}, raiseE=False)
    False
    """
    if type(var) == type(''):
        #if re.match('^[a-zA-Z0-9_?()[\] ]*$', var) == None:
        if re.match('^[a-zA-Z0-9_?()[\] "]*$', var) == None:
            if raiseE:
                raise InsecureVariable(var)
            return False
        return True
    elif type(var) == type([]):
        for item in var:
            if not testVarSecurity(item, raiseE):
                return False
        return True
    elif type(var) == type({}):
        if var.has_key('self'):  # for call with locals()
            var.pop('self')
        return testVarSecurity(var.values(), raiseE)
    elif type(True):
        return True
    else:
        assert False, 'Unknown type of input: ' + str(type(var))


def format_flr(filename, writeback=False):
    """formats an flr-file
       especially useful after using floras _save(file) command
    """

    """read & parse
        * ignore comments
        * ignore newlines
        * put rules into one line each
    """
    content = []
    fd = open(filename, 'r')
    line = fd.readline()
    while line != '':
        line = line.strip()
        if len(line) != 0 \
        and line[0] != '/':  # comment 
            content.append(line)
            if line.endswith(' :-'):  # rule
                content[-1] += ' ' + fd.readline().strip()
        line = fd.readline()

    """sort"""
    content.sort(comperator)

    """replace Vars"""
    import re
    for nr in range(len(content)):
        variables = list(set([x.group() for x in re.finditer('[?]_h[0-9]*', content[nr])]))
        variables.sort()
        content[nr] = content[nr].replace('??', '?')
        assert len(variables) <= 36, 'Implement naming of vars…'
        for var in variables:
            content[nr] = content[nr].replace(var, '?' + chr(variables.index(var)+65))
   
    """compress facts belonging together"""

    """spacing?"""
 
    """rewrite and return""" 
    if writeback:
        open(filename, 'w').writelines([l + '\n' for l in content])
    return content


def comperator(x, y):
    """helper function for sorting flora-facts/rules"""
    order = [':', '[', '{', '=', '-'] + [chr(char) for char in range(97, 123)]
    args = [x[:1], y[:1]]
    args.sort()
    order += args
    result = order.index(x[:1]) - order.index(y[:1])
    if result == 0:
        if len(x[1:]) == 0 or len(y[1:]) == 0:
            return len(x) - len(y)
        return comperator(x[1:], y[1:])
    return result / abs(result)


if __name__ == '__main__':
    result = doctest.testmod()
    print result
    sys.exit(result.failed)
