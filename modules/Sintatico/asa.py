class node:
    def __init__(self,token,level=0):
        self.token = token
        self.level = level
        self.fields = {}

    def add_children(self,field,tokens):
        if field not in self.fields:
            self.fields[field] = []

        for t in tokens:
            self.fields[field].append(node(t,self.level+1))

        return self.fields[field]

    def __repr__(self):
        print(f'{' '*self.level}{self.token}')
        for child in self.fields:
            print(child)

class ASA:
    def __init__(self,stack):
        self.stack = stack
        self.root = self.process(self.stack)

    def process(self,stack):
        pass

    def __repr__(self):
        print(self.root)
        