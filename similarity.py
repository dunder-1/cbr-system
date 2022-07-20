import math

def manhattan_sim(q_val: float, c_val: float) -> float:
    m_dist = lambda x, y: abs(x - y)
    return 1 / (1 + m_dist(q_val, c_val))

def euclid_sim(q_val: float, c_val: float) -> float:
    e_dist = lambda x, y: math.sqrt((x - y)**2)
    return 1 / (1 + e_dist(q_val, c_val))

def edit_distance(word_1: str, word_2: str, to_same_case: bool = True) -> int:

    if word_1 == word_2:
        return 0

    if to_same_case:
        word_1, word_2 = [word.upper() for word in (word_1, word_2)]
    
    word_1, word_2 = list(word_1), list(word_2)
    longer_word = word_1 if len(word_1) > len(word_2) else word_2

    i, count = 0, 0
    while i < len(longer_word):
        
        # word_2 is longer -> add current char of word_2
        if i >= len(word_1):
            word_1.append(word_2[i])
            count += 1
            #continue

        # word_1 is longer -> remove current char of word_1
        if i >= len(word_2):
            word_1.pop(i)
            count += 1
            continue

        # same char -> skip word
        if word_1[i] == word_2[i]:
            i += 1
            continue

        # not in the beginning or the end
        if i > 0 and i < len(word_1):
            # previous char is same and current char of word_1 is same as next char of word_2
            # -> fill current char of word_2 between last and next char of word_1
            # e.g. word_1[i-1] = "M" ;                   word_1[i]   = "R"
            #      word_2[i-1] = "M" ; word_1[i] = "A" ; word_2[i+1] = "R"     
            if word_1[i-1] == word_2[i-1] and word_1[i] == word_2[i+1]:
                word_1.insert(i, word_2[i])
                count += 1
                i += 1
                continue

        if word_1[i] != word_2[i]:
            word_1.pop(i)
            count += 1
            continue

    return "".join(word_1), count

