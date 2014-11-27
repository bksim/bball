#!/usr/bin/python
'''
Simplest OpenOpt KSP example;
requires FuncDesigner installed.
For some solvers limitations on time, cputime, "enough" value, basic GUI features are available.
See http://openopt.org/KSP for more details
'''
from openopt import *
import csv
from pprint import pprint


def load_projections(projections_file):
    projections = {}
    with open(projections_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            projections[row[0]] = float(row[1])
    return projections
        

def optimizer(projections=None, site="DraftKings"):

    adjustments = {'Kevin Martin': 0.0, #injury
                   'Derrick Rose': 0.0, #crap player
                   'Stephen Curry': 0.0
                  }

    items = []
    player_ids = {}

    with open('DKSalaries_11272014.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        index = 0
        for row in reader:
            if index != 0:
                vals = { 
                        'id': index-1,
                        'PG': 1 if row[0] == 'PG' else 0,
                        'SG': 1 if row[0] == 'SG' else 0,
                        'SF': 1 if row[0] == 'SF' else 0,
                        'PF': 1 if row[0] == 'PF' else 0,
                        'C': 1 if row[0] == 'C' else 0,
                        'name': row[1],
                        'salary': int(row[2]),
                        'fpts': float(row[4]) if row[1] not in adjustments.keys() else adjustments[row[1]]
                        }
                vals['PGSGC'] = vals['PG'] + vals['SG'] + vals['C']
                vals['PFSFC'] = vals['PF'] + vals['SF'] + vals['C']
                if projections != None:
                    vals['fpts'] = projections[vals['name']]
                items.append(vals)
            index += 1

    for item in items:
        for i in range(len(items)):
            item['id%d' % i] = float(item['id'] == i)

    constraints = lambda values: (
                              values['salary'] < 50000, 
                              values['nItems'] == 8, 
                              values['PG'] >= 1,
                              values['PG'] <= 2,
                              values['SG'] >= 1,
                              values['SG'] <= 2,
                              values['SF'] >= 1,
                              values['SF'] <= 2,
                              values['PF'] >= 1,
                              values['PF'] <= 2,
                              values['PFSFC'] >= 4,
                              values['PFSFC'] <= 5,
                              values['PGSGC'] >= 4,
                              values['PGSGC'] <= 5,
                             ) + tuple([values['id%d'% i] <= 1 for i in range(len(items))])


                                  # we could use lambda-func, e,g.
                                  # values['mass'] + 4*values['volume'] < 100
    objective = 'fpts'
    # we could use lambda-func, e.g. 
    # objective = lambda val: 5*value['cost'] - 2*value['volume'] - 5*value['mass'] + 3*val['nItems']
    p = KSP(objective, items, goal = 'max', constraints = constraints) 
    r = p.solve('glpk', iprint = 0) # requires cvxopt and glpk installed, see http://openopt.org/KSP for other solvers
    ''' Results for Intel Atom 1.6 GHz:
    ------------------------- OpenOpt 0.50 -------------------------
    solver: glpk   problem: unnamed    type: MILP   goal: max
     iter   objFunVal   log10(maxResidual)   
        0  0.000e+00               0.70 
        1  2.739e+01            -100.00 
    istop: 1000 (optimal)
    Solver:   Time Elapsed = 0.82   CPU Time Elapsed = 0.82
    objFunValue: 27.389749 (feasible, MaxResidual = 0)
    '''
    print(r.xf) 