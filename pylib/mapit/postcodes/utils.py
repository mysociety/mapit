import re

def is_valid_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    # Our test postcode
    if pc in ('ZZ99ZZ', 'ZZ99ZY'): return True
    
    # See http://www.govtalk.gov.uk/gdsc/html/noframes/PostCode-2-1-Release.htm
    inward  = 'ABDEFGHJLNPQRSTUWXYZ'
    fst = 'ABCDEFGHIJKLMNOPRSTUWYZ'
    sec = 'ABCDEFGHJKLMNOPQRSTUVWXY'
    thd = 'ABCDEFGHJKSTUW'
    fth = 'ABEHMNPRVWXY'

    if re.match('[$fst][1-9]\d[$in][$in]$', pc) or \
        re.match('[$fst][1-9]\d\d[$in][$in]$', pc) or \
        re.match('[$fst][$sec]\d\d[$in][$in]$', pc) or \
        re.match('[$fst][$sec][1-9]\d\d[$in][$in]$', pc) or \
        re.match('[$fst][1-9][$thd]\d[$in][$in]$', pc) or \
        re.match('[$fst][$sec][1-9][$fth]\d[$in][$in]$', pc):
        return True

    return False

def is_valid_partial_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    # Our test postcode
    if pc == 'ZZ9': return True
    
    # See http://www.govtalk.gov.uk/gdsc/html/noframes/PostCode-2-1-Release.htm
    fst = 'ABCDEFGHIJKLMNOPRSTUWYZ'
    sec = 'ABCDEFGHJKLMNOPQRSTUVWXY'
    thd = 'ABCDEFGHJKSTUW'
    fth = 'ABEHMNPRVWXY'
  
    if re.match('[$fst][1-9]$', pc) or \
        re.match('[$fst][1-9]\d$', pc) or \
        re.match('[$fst][$sec]\d$', pc) or \
        re.match('[$fst][$sec][1-9]\d$', pc) or \
        re.match('[$fst][1-9][$thd]$', pc) or \
        re.match('[$fst][$sec][1-9][$fth]$', pc):
        return True

    return False

