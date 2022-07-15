def printHello
  puts "Hello"
  # OP_ENTER:  req: 0 opt: 0 rest: 0 post: 0 key: 0 kdict: 0 block: 0
end

def notA(a)
  # OP_ENTER:  req: 1 opt: 0 rest: 0 post: 0 key: 0 kdict: 0 block: 0
  !a
end

def aPlusB(a, b)
  # OP_ENTER:  req: 2 opt: 0 rest: 0 post: 0 key: 0 kdict: 0 block: 0
  res = a + b
  return res
end

def aPlusBPlusC(a, b, c)
  # OP_ENTER:  req: 3 opt: 0 rest: 0 post: 0 key: 0 kdict: 0 block: 0
  res = a + b + c
  return res
end

def aMultB(a, b = 1.0, c = 2.0)
  # OP_ENTER:  req: 1 opt: 1 rest: 0 post: 0 key: 0 kdict: 0 block: 0
  return 1
  res = a * b
  return res
end

def printAll(prefix, *args)
  # OP_ENTER:  req: 1 opt: 0 rest: 1 post: 0 key: 0 kdict: 0 block: 0
  args.each do |arg|
    # OP_ENTER:  req: 1 opt: 0 rest: 0 post: 0 key: 0 kdict: 0 block: 0
    puts "#{prefix} #{arg}"
  end
end

def methodWithBlockParam(a, b, &block)
  # OP_ENTER:  req: 2 opt: 0 rest: 0 post: 0 key: 0 kdict: 0 block: 1
  block.call(a, b)
end
