module MyMod
    module NestedMod
        class Class1
        end
    end
end

class Class2
    def printHello
        puts "Hello"
    end
end

class Class3 < Class2
    def test
        x = 1
        y = 2
        puts (x + y)
    end
end

class Class4
    @@y = 2

    def initialize
        @x = 1
    end
    def test
        puts (@x + @@y)
    end
end

class Class5
    def self.single
    end
end

test = Class5.new
def test.single2
end
class << test
    def single3
    end
end

