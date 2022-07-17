import math
from model import Query, Case

def manhattan_sim(q_val: float, c_val: float) -> float:
    m_dist = lambda x, y: abs(x - y)
    return 1 / (1 + m_dist(q_val, c_val))

def euclid_sim(q_val: float, c_val: float) -> float:
    e_dist = lambda x, y: math.sqrt((x - y)**2)
    return 1 / (1 + e_dist(q_val, c_val))

def edit_distance():
    pass

def calc_similarity(function, query: Query, case: Case, field: str) -> float:
    return function(query.problem[field], case.problem[field])