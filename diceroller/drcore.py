# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import sys
import string
import random

import string,operator
ops      = [operator.add,operator.sub,operator.mul,operator.div]

global explode 
global print_cb
global reroll_1
global explode_once

''' Algorithms '''
def set_reroll_1(flag):
    global reroll_1
    reroll_1 = flag
    
def set_explode(value):
    global explode
    explode = value
    
def set_explode_once(value):
    global explode_once
    explode_once = value    
    
def set_output_cb(cb):
    global print_cb
    print_cb = cb
    
def out_print(str_):
    if print_cb is None:
        print str_
    else:
        print_cb(str_)
    
def math_to_rpn(ex_string):
    my_opers = []
    my_rpn = ''

    for ch in ex_string:
        #print my_opers
        # se e' una parentesi la impiliamo sullo stack
        if ch == '(':
            my_opers.append(ch)
        # se invece e' un numero lo accodiamo alla sequenza rpn
        elif ch.isdigit() or ch == '.':
            my_rpn += ch
        # se infine e' un operatore le cose si complicano....
        elif string.find('+-*/dk', ch) >= 0:
            ''' se lo stack e' vuoto oppure il l'operatore che viene prima e'
                una parentesi o ha precedenza minore, impilo quello attuale sullo stack '''
            if len(my_opers) == 0 or peek(my_opers) == '(' or get_op_val(peek(my_opers)) < get_op_val(ch):
                my_opers.append(ch)
            else:
                ''' altrimenti riversa lo stack degli operatori sulla sequenza rpn fino a che non troviamo
                    una parentesi aperta o un operatore con precedenza minore a quello attuale '''
                while True:
                    my_rpn += ' '
                    my_rpn += my_opers.pop()
                    if len(my_opers) == 0 or peek(my_opers) == '(' or get_op_val(ch) > get_op_val(peek(my_opers)):
                        break;

                # alla fine mettiamo anche questo operatore nello stack
                my_opers.append(ch)
            my_rpn += ' '
        # se trovo una parentesi chiusa, svuoto lo stack fino alla prossima parentesi aperta
        elif ch == ')':
            while peek(my_opers) != '(':
                my_rpn += ' '
                my_rpn += my_opers.pop()
            # e poi tolgo dallo stack la parentesi aperta corrispondente
            my_opers.pop()


    # infine se c'e' ancora qualcosa nello stack, lo svuoto nella sequenza rpn
    while len(my_opers) > 0:
        my_rpn += ' '
        my_rpn += my_opers.pop()

    return my_rpn

def rpn_solve(ex_string):
    value = 0.0
    #print 'parsing: ' + ex_string
    try:
        st = []
        for tk in string.split(ex_string):
            oi = string.find('+-*/',tk)
            if len(tk)==1 and oi>=0:
                y,x = st.pop(),st.pop()
                z = ops[oi](x,y)
                out_print('%s %s %s => %s' % (repr(x), str(tk),repr(y),repr(z)))
            elif len(tk)==1 and tk=='d':
                y,x = st.pop(),st.pop()
                z = roll_dices(int(x),int(y))
                out_print('Rolled %dd%d => %d' % (int(x),int(y),int(z)))
            elif len(tk)==1 and tk=='k':
                # l5r roll and keep
                k, r = st.pop(),st.pop()
                z = roll_l5r_pool(int(r), int(k))
                out_print('Rolled %dk%d => %d' % (int(r),int(k),int(z)))
            else:
                z = float(tk)
            st.append(z)
        assert len(st)<=1
        if len(st)==1:
            value = st.pop()
    except Exception, reason:  print reason
    return value

def get_op_val(ch_oper):
    if ch_oper == '+' or ch_oper == '-':
        return 1
    elif ch_oper == 'd':
        return 4
    elif ch_oper == 'k':
        return 5        
    elif ch_oper == '*' or ch_oper == '/':
        return 3
    else:
        return 0

def roll_dices(dices,face):
    value = 0
    print 'rolling ' + str(dices) + ' with ' + str(face) + ' faces'
    for i in range(0,dices):
        roll = random.randint(1,face)
        #out_print('obtained %d' % roll)
        value += roll
    return value
    
def roll_l5r_pool(pool, keep):    
    rolls     = []
    print 'rolling ' + str(pool) + ' and keep ' + str(keep) + ' dices'
    for i in range(0,pool):
        roll     = 0
        tot_roll = 0
        while ( roll == 0 or roll >= explode ):
            old_roll  = roll
            roll      = random.randint(1,10)
            tot_roll += roll
            if (reroll_1 and tot_roll == roll and 
                roll == 1):
                # reroll 1s                
                roll      = random.randint(1,10)
                out_print('rerolled an 1 into a %d' % roll)
                tot_roll  = roll
            
            if old_roll >= explode:
                out_print('exploded %d to %d' % (old_roll, tot_roll))
            
            if explode_once and tot_roll != roll:
                break
                        
        #out_print('obtained %d' % tot_roll)        
        #print 'obtained ' + str(tot_roll)
        rolls.append(tot_roll)
        
    rolls.sort()
    print 'rolls: %s' % rolls
    value = sum( rolls[-keep:] )
    out_print('from %dk%d %s kept %s' % (pool,keep,rolls,rolls[-keep:]))
    print 'total value = %d' % value
    return value
    
def peek(stack):
    return stack[len(stack)-1]
    
def test():
    expr = '4k2'
    rpn  = math_to_rpn(expr)
    print rpn
    val  = rpn_solve(rpn)
    print val
    
if __name__ == '__main__':
    test()