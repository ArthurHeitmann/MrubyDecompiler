def printHello
  puts "Hello"
end

def notA(a)
  !a
end

def aPlusB(a, b)
  res = a + b
  return res + 1
end

def aPlusBPlusC(a, b, c)
  res = a + b + c
  return res
end

def aMultB(a, aa, aaa, b = 1.0, c = 2.0)
  res = a * b
  return res
end

def printAll(prefix, *args)
  args.each do |arg|
    puts "#{prefix} #{arg}"
  end
end

def methodWithBlockParam(a, b, &block)
  block.call(a, b)
end

offset = 2
(1..3).each { |i| puts i + offset }
(1..3).each { puts }
(1...3).each do |i| puts "YEP#{i}" end
(1...3).each do puts end

myHash = { "a" => 1, :b => 2, "c" => 3 }

for i in 1..5
  puts i
end
for k, v in myHash
  puts "#{k} => #{v + offset}"
  offset += 1
end

myHash.each { |k, v| puts "#{k} => #{v + offset}" }
