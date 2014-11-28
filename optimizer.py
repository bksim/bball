import subprocess, StringIO
import csv
import os

# load data about salaries
# fn: file with salaries
# projections: model projections
# adjustments: discretionary set of adjustments
def load_data(fn, projections, adjustments):
    items = []
    with open(fn) as f:
        reader = csv.reader(f)
        index = 0
        for row in reader:
            if index != 0:
                vals = {
                        'id': 'P' + str(index),
                        'PG': 1 if row[0] == 'PG' else 0,
                        'SG': 1 if row[0] == 'SG' else 0,
                        'SF': 1 if row[0] == 'SF' else 0,
                        'PF': 1 if row[0] == 'PF' else 0,
                        'C': 1 if row[0] == 'C' else 0,
                        'position': row[0],
                        'name': row[1],
                        'salary': int(row[2]),
                        'fpts': float(row[4]) if row[1] not in adjustments else adjustments[row[1]]
                        }
                if projections != None:
                    # adjustments take precedence over model
                    if vals['name'] not in adjustments:
                        # makes sure our model has a projection for the player before using it
                        if vals['name'] in projections:
                            vals['fpts'] = projections[vals['name']]
                items.append(vals)
            index += 1
    return items
    
# takes a list of items from load_data and maximizes EV
def objective_function(items):   
    m = " + ".join("{ev} {pid}".format(ev=p['fpts'], pid=p['id']) for p in items)
    return "max: " + m + ";\n"

# cost constraints
def cost_constraint(items, max_salary):
    c = " + ".join("{cost} {pid}".format(cost=p['salary'], pid=p['id']) for p in items)
    return "cost_constraint: " + c + " <= %s;\n" % max_salary

# position constraints
def position_constraints(items):
    constraints = StringIO.StringIO()
    
    # total players = 8
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in items) + " = 8;\n")
    
    # 2 >= pgs >= 1
    pgs = [p for p in items if p['position'] == 'PG']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in pgs) + " >= 1;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in pgs) + " <= 2;\n")

    # 2 >= sgs >= 1
    sgs = [p for p in items if p['position'] == 'SG']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in sgs) + " >= 1;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in sgs) + " <= 2;\n")
    
    # 2 >= sfs >= 1 
    sfs = [p for p in items if p['position'] == 'SF']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in sfs) + " >= 1;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in sfs) + " <= 2;\n")
    
    # 2 >= pfs >= 1
    pfs = [p for p in items if p['position'] == 'PF']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in pfs) + " >= 1;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in pfs) + " <= 2;\n")
    
    # 2 >= c >= 1
    cs = [p for p in items if p['position'] == 'C']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in cs) + " >= 1;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in cs) + " <= 2;\n")
    
    # 5 >= pgs+sgs+c >= 4
    pgsgc = [p for p in items if p['position'] == 'PG' or p['position'] == 'SG' or p['position'] == 'C']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in pgsgc) + " >= 4;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in pgsgc) + " <= 5;\n")
    
    # 5 >= sfs+pfs+c >= 4
    sfpfc = [p for p in items if p['position'] == 'SF' or p['position'] == 'PF' or p['position'] == 'C']
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in sfpfc) + " >= 4;\n")
    constraints.write(" + ".join("{pid}".format(pid=p['id']) for p in sfpfc) + " <= 5;\n")
    
    return constraints.getvalue()

# declares all players to be binary variables
def all_player_variables(items):
    variables = ", ".join("{pid}".format(pid=p['id']) for p in items)
    return "bin %s;\n" % variables

# returns top lineup(s) given a set of projections, salaries, and adjustments
# fn: DK salary file
# projections: a dictionary with keys: player names and values: projected FP
# adjustments: a dictionary with keys: player names 
def run_optimization(fn, projections, adjustments, num_lineups):
    results = []
    old_constraints = []
    items = load_data(fn, projections, adjustments)
    p_ids = [p['id'] for p in items]
    
    for i in range(num_lineups):
        lp = StringIO.StringIO()
        lp.write(objective_function(items))
        lp.write(cost_constraint(items, 50000))
        lp.write(position_constraints(items))
        
        # write old constraints to prevent getting the same team to get the top N results
        for c in old_constraints:
            lp.write(c)
        
        lp.write(all_player_variables(items))
    
        # SUPPOSEDLY supposed to use StringIO to avoid writing a temp file, but can't figure it out right now
        # writes a temp file, still works
        temp_fn = 'templpfile'
        with open(temp_fn, 'wb') as f:
            f.write(lp.getvalue())
        if (os.name == 'posix'): #check if linux/unix
            cmd = './lp_solve ' + temp_fn
        else: #windows 
            cmd = "lp_solve " + temp_fn
        val = subprocess.check_output(cmd, shell=True).split('\n')
        team = []
        pid_team = []
        for v in val:
            temp = v.split()
            if len(temp) > 0:
                if temp[0][0] == 'P':
                    if temp[1] == '1':
                        team.append(items[p_ids.index(temp[0])]['name'])
                        pid_team.append(temp[0])
                elif temp[0][0] == 'V':
                    obj_func_value = float(v.split(':')[1].rstrip('\r'))
        r = {'team': team, 
                        'value': obj_func_value, 
                        'old_constraints': " + ".join(pid_team) + " <= " + str(len(pid_team)-1) + ";\n"}
        results.append(r)
        old_constraints.append(r['old_constraints'])
    return results
