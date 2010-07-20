import re

def is_valid_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    # Our test postcode
    if pc in ('ZZ99ZZ', 'ZZ99ZY'): return True
    
    # See http://www.govtalk.gov.uk/gdsc/html/noframes/PostCode-2-1-Release.htm
    inward = 'ABDEFGHJLNPQRSTUWXYZ'
    fst = 'ABCDEFGHIJKLMNOPRSTUWYZ'
    sec = 'ABCDEFGHJKLMNOPQRSTUVWXY'
    thd = 'ABCDEFGHJKSTUW'
    fth = 'ABEHMNPRVWXY'

    if re.match('[%s][1-9]\d[%s][%s]$' % (fst, inward, inward), pc) or \
        re.match('[%s][1-9]\d\d[%s][%s]$' % (fst, inward, inward), pc) or \
        re.match('[%s][%s]\d\d[%s][%s]$' % (fst, sec, inward, inward), pc) or \
        re.match('[%s][%s][1-9]\d\d[%s][%s]$' % (fst, sec, inward, inward), pc) or \
        re.match('[%s][1-9][%s]\d[%s][%s]$' % (fst, thd, inward, inward), pc) or \
        re.match('[%s][%s][1-9][%s]\d[%s][%s]$' % (fst, sec, fth, inward, inward), pc):
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
  
    if re.match('[%s][1-9]$' % fst(), pc) or \
        re.match('[%s][1-9]\d$' % (fst), pc) or \
        re.match('[%s][%s]\d$' % (fst, sec), pc) or \
        re.match('[%s][%s][1-9]\d$' % (fst, sec), pc) or \
        re.match('[%s][1-9][%s]$' % (fst, thd), pc) or \
        re.match('[%s][%s][1-9][%s]$' % (fst, sec, fth), pc):
        return True

    return False

