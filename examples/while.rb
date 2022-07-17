x = 1 + 2

until x == 3
  puts x
  x += 1
end

while MyMod::X < 42 && rand() < 0.5 || x == 3
  puts "Hello World"
end

while x < 10
    puts x
    x += 1
    if x == 6
        next
    end
end

while x < 20
    if x == 15
        break
    end
end

while true
    for i in 1..10
        if i == 5
            while i < 10
                puts i
                i += 1
            end
        end
        puts i
    end
end

def test
    if rand()
        return
    end
    for i in 1..10
        if i == 5
            next
        elsif i == 8
            break
        elsif i == 9
            return
        end
        puts i
    end
end