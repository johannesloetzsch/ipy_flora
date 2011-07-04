#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This file provides:
* an test to see if everything was correctly installed 
  (just run it with >python ./test_and_tutorial.py)
* a tutorial-like example showing how (I)Python and Flora can work together


# commands usable in ipython are here written as doctests
# just type in ipython what you see within
>>> r('         ') 

# Let's start…


# add a fact
>>> r(' ++ f1:Function[s -> "leet*pi/100"] ')
[insert]

# add another fact and substitude python-variable in flora-expression
>>> r(' leet = 1337 ')
>>> r(' ++ f2:Function[s -> "$leet/pi/10"] ')
[insert]

# this time substitute by result of python-compound
>>> r(' leetspeak = lambda string: string.replace("l", "1").replace("e", "3").replace("t", "7") ')
>>> r(' ++ f3:Function[s -> "sqrt(${leetspeak("leet")}**2/10)/10"] ')
[insert]

# now query flora for the previous entered facts
>>> r(' ?- ?F:Function[s -> ?S] ')
[refresh: ?F:Function[s -> ?S]]
[query for ['S', 'F']]
[{'F': 'f1', 'S': 'leet*pi/100'},
 {'F': 'f2', 'S': '1337/pi/10'},
 {'F': 'f3', 'S': 'sqrt(1337**2/10)/10'}]

# and access the last result via _-variable
>>> r(' dict([(item["F"], item["S"]) for item in _]) ')
{'f1': 'leet*pi/100', 'f2': '1337/pi/10', 'f3': 'sqrt(1337**2/10)/10'}

# let's save this to variable, since _ will be overwritten…
>>> r(' remembered = _ ')

# calculate results of our functions
>>> r(' from math import pi, sqrt ')
>>> r(' calculated = [int(eval(remembered[k])) for k in remembered] ')

# write results into our flora knowledge-base
>>> r(' keys = remembered.keys() ')
>>> r(' values = calculated[:] ')
>>> r(' _ = [_ip.IP.runlines("++ ${keys.pop()}[answer -> ${values.pop()}]") for item in remembered] ')
[insert]
[insert]
[insert]

# query flora for function which results in given range
>>> r(' ?- ?_F:Function[answer -> ?_A], ?_F:Function[s -> ?INRANGE], ?_A > 23, ?_A < $leet ')
[unrefreshable]
[query for ['INRANGE']]
['1337/pi/10', 'leet*pi/100', 'sqrt(1337**2/10)/10']

# look for functions wich are unique in having this result
>>> r(' ++ ?F[unique_answer -> ?A] :- ?F:Function[answer -> ?A],\
                                      not (( ?F2:Function[answer -> ?A], not ?F2 :=: ?F )) ')
[insertrule]
>>> r(' ?- ?F[unique_answer -> ?A] ')
[refresh: ?F[unique_answer -> ?A]]
[query for ['A', 'F']]
[]

# no function has another result than the other ones???
# let's ask for the ultimative answer of everything…
>>> r(' ++ AnswerOnEverything[answer -> ?A] :- ?_:Function[answer -> ?A], not ?_:Function[unique_answer -> ?_] ')
[insertrule]
>>> r(' ?- AnswerOnEverything[answer -> ?AnswerToEverything] ')
[refresh: AnswerOnEverything[answer -> ?AnswerToEverything]]
[query for ['AnswerToEverything']]
['42']

# What would happen when inserting some other result?
# for example when doing this calculations without rounding?

# We change our calculation
>>> r(' calculated = [eval(remembered[k]) for k in remembered] ')

# And redo from history
#>>> r(' _ip.IP.magic_hist("-f .history -r") ')
#>>> r(' rm .history -f')
#>>> r(' _ip.IP.magic_rep("12-13") ')
>>> r(' keys = remembered.keys() ')
>>> r(' values = calculated[:] ')
>>> r(' _ = [_ip.IP.runlines("++ ${keys.pop()}[answer -> ${values.pop()}]") for item in remembered] ')
[insert]
[insert]
[insert]

# Now both answers are stored for all questions, because we did not remove the old ones
>>> r(' ?- ?Answers = collectset{ ?_A[?F] | ?F:Function[answer->?_A] } ')
[unrefreshable]
[query for ['Answers', 'F']]
[{'Answers': '[42.0030937785, 42]', 'F': 'f1'},
 {'Answers': '[42.2795458821, 42]', 'F': 'f3'},
 {'Answers': '[42.5580317828, 42]', 'F': 'f2'}]

# We can fix this
>>> r(' -- ?_[answer -> 42] ')
[deleteall]
>>> r(' ?- ?F:Function[answer -> ?A] ')
[refresh: ?F:Function[answer -> ?A]]
[query for ['A', 'F']]
[{'A': '42.0030937785', 'F': 'f1'},
 {'A': '42.2795458821', 'F': 'f3'},
 {'A': '42.5580317828', 'F': 'f2'}]

# What about the AnswerOnEverything Answer now?
>>> r(' ?- AnswerOnEverything[answer -> ?AnswerToEverything] ')
[refresh: AnswerOnEverything[answer -> ?AnswerToEverything]]
[query for ['AnswerToEverything']]
['42.0030937785', '42.2795458821', '42.5580317828']

# Why???
# Because of tabling (caching of sub-answers for better performance)

# Let's look what flora thinks about „not having a unique_answer“
# (this was part of our definition for AnswerOnEverything)
# For learning about internals we use this low-level way to query first:
>>> r(' _ip.IP.flora_instance.query("not ?_:Function[unique_answer -> ?_].") ')
[{}]
>>> r(' ?- not ?_:Function[unique_answer -> ?_] ')
[unrefreshable]
[query for []]
True

# Now we explicitly clean the cache (abolish_all_tables)
>>> r(' _ip.IP.magic_flora_abolish_all_tables(None) ')

# And ask again…
>>> r(' _ip.IP.flora_instance.query("not ?_:Function[unique_answer -> ?_].") ')
[]
>>> r(' ?- not ?_:Function[unique_answer -> ?_] ')
[unrefreshable]
[query for []]
False
>>> r(' ?- AnswerOneverything[answer -> ?AnswerToEverything] ')
[refresh: AnswerOneverything[answer -> ?AnswerToEverything]]
[query for ['AnswerToEverything']]
[]

# …
"""

import IPython
import sys
import pprint
import doctest
import subprocess


def r( cmd ):
    """some definitions allowing us to write ipython-syntax within doctests"""
    sys.displayhook = ipy.sys_displayhook_embed
    _ip.IP.runlines( cmd )
    sys.displayhook = sys.__displayhook__
    if Out.has_key(len(In)-1):
        pprint.pprint(_)


if __name__ == '__main__':
    print 'Run Selftest…'

    for test in ['rpsimple', 'ipy_flora']:
        print '\n===test ' + test + '==='
        failed = subprocess.call('./ipy_flora/' + test + '.py')
        assert failed == 0, 'Error while testing of ' + test + '\n' \
                'Please assure that you installed correctly like described in README'

    print '\n===test tutorial==='
    (_, __, ___) = (None, None, None)  # export this variables to IPython
    ipy = IPython.Shell.IPShellEmbed(user_ns=locals())

    warnings = ''
    if not hasattr(ipy.IP, 'flora_instance'):
        warnings += '\nYou should load „ipy_flora“ from your IPython-config — see INSTALL'
        ipy.IP.api.load('ipy_flora.ipy_flora')

    result = doctest.testmod(extraglobs=locals())
    print result 
    assert result.failed == 0, 'Error while testing tutorial'
    #ipy()  # can be used for debugging
    
    print warnings

    print '\nEverything seems to work :)'
    print 'Now you can read the content of test_and_tutorial.py and do everything step by step yourself…'
