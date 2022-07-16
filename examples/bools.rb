v1 = someRand
v2 = someRand
v3 = someRand
v4 = someRand

# # tmp = v1
# # JMPNOT tmp + 2
# # tmp = v2
# # var = tmp
var = v1 && v2
# tmp = nil
# tmp = nil
# # tmp = v1
# # JMPIF tmp + 2
# # tmp = v2
# # var = tmp
var = v1 || v2
# tmp = nil
# tmp = nil
# # tmp = v1
# # JMPNOT tmp + 2    AND
# # tmp = v2
# # JMPIF tmp + 2     OR
# # tmp = v3
# # var = tmp
var = v1 && v2 || v3
# tmp = nil
# tmp = nil
# # tmp = v1
# # JMPNOT tmp + 4    AND
# # tmp = v2
# # JMPIF tmp + 2     OR
# # tmp = v3
# # var = tmp
var = v1 && (v2 || v3)
# tmp = nil
# tmp = nil
# # tmp = v1
# # JMPNOT tmp + 4    AND
# # tmp = v2
# # JMPIF tmp + 2     OR
# # tmp = v3
# # JMPNOT tmp + 2    AND
# # tmp = v4
# # var = tmp
var = v1 && (v2 || v3) && v4
# tmp = nil
# tmp = nil
# # tmp = v1
# # JMPNOT tmp + 4    AND
# # tmp = v2
# # JMPIF + 2         OR
# # tmp = v4
# # JMPNOT tmp + 2    AND
# # tmp = v3
# # JMPIF tmp + 2     OR
# # tmp = v4
# # var = tmp
var = v1 && (v2 || v4) && v3 || var
