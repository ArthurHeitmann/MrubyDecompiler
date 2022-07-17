v1 = someRand

case v1
when 1, 2, rand1() || rand(), 4
    var = []
when 2, 3
    var = v1 + 2
when 4
    var = v1 || nil
else
    var = v1
end

puts "yep"

case
when someFun()
    var = v1
when someFun2()
    var = []
# else
#     var = v1
end

x = []

puts var
