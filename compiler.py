from defs import *
from model import *
from tokens import *
from utils import *

SYM_VAR  = 'SYM_VAR'
SYM_FUNC = 'SYM_FUNC'

class Symbol:
  def __init__(self, name, symtype=SYM_VAR, depth=0, arity=0):
    self.name = name
    self.depth = depth
    self.symtype = symtype
    self.arity = arity

class Compiler:
  def __init__(self):
    self.code = []
    self.locals = []
    self.globals = []
    self.functions = []
    self.scope_depth = 0
    self.label_counter = 0

  def make_label(self):
    self.label_counter += 1
    return f'LBL{self.label_counter}'

  def emit(self, instruction):
    self.code.append(instruction)

  def get_func_symbol(self, name):
    # Loop the function list trying to find the first occurrence of that symbol name
    for symbol in reversed(self.functions):
      if symbol.name == name:
        return symbol

  def get_var_symbol(self, name):
    # Loop the locals list in reversed order, trying to find the first occurrence of that symbol name
    for index, symbol in reversed(list(enumerate(self.locals))):
      if symbol.name == name:
        return (symbol, index)
    # Loop the globals list in reversed order, trying to find the first occurrence of that symbol name
    for index, symbol in reversed(list(enumerate(self.globals))):
      if symbol.name == name:
        return (symbol, index)
    return None

  def begin_block(self):
    self.scope_depth += 1

  def end_block(self):
    self.scope_depth -= 1
    # Loop and remove all the locals that are "deeper" than the current scope depth
    i = len(self.locals) - 1
    while len(self.locals) > 0 and self.locals[i].depth > self.scope_depth:
      self.emit(('POP',))
      self.locals.pop()
      i -= 1
    # Loop and remove all the functions that were declared in a "deeper" scope than the current scope depth
    i = len(self.functions) - 1
    while len(self.functions) > 0 and self.functions[i].depth > self.scope_depth:
      self.functions.pop()
      i -= 1

  def compile(self, node):
    if isinstance(node, Integer):
      value = (TYPE_NUMBER, float(node.value))
      self.emit(('PUSH', value))

    elif isinstance(node, Float):
      value = (TYPE_NUMBER, float(node.value))
      self.emit(('PUSH', value))

    elif isinstance(node, Bool):
      value = (TYPE_BOOL, True if node.value == True or node.value == 'true' else False)
      self.emit(('PUSH', value))

    elif isinstance(node, String):
      value = (TYPE_STRING, stringify(node.value))
      self.emit(('PUSH', value))

    elif isinstance(node, BinOp):
      self.compile(node.left)
      self.compile(node.right)
      if node.op.token_type == TOK_PLUS:
        self.emit(('ADD',))
      elif node.op.token_type == TOK_MINUS:
        self.emit(('SUB',))
      elif node.op.token_type == TOK_STAR:
        self.emit(('MUL',))
      elif node.op.token_type == TOK_SLASH:
        self.emit(('DIV',))
      elif node.op.token_type == TOK_CARET:
        self.emit(('EXP',))
      elif node.op.token_type == TOK_MOD:
        self.emit(('MOD',))
      elif node.op.token_type == TOK_LT:
        self.emit(('LT',))
      elif node.op.token_type == TOK_GT:
        self.emit(('GT',))
      elif node.op.token_type == TOK_LE:
        self.emit(('LE',))
      elif node.op.token_type == TOK_GE:
        self.emit(('GE',))
      elif node.op.token_type == TOK_EQEQ:
        self.emit(('EQ',))
      elif node.op.token_type == TOK_NE:
        self.emit(('NE',))

    elif isinstance(node, UnOp):
      self.compile(node.operand)
      if node.op.token_type == TOK_MINUS:
        self.emit(('NEG',))
      elif node.op.token_type == TOK_NOT:
        self.emit(('PUSH', (TYPE_BOOL, True)))
        self.emit(('XOR',))

    elif isinstance(node, LogicalOp):
      self.compile(node.left)
      self.compile(node.right)
      if node.op.token_type == TOK_AND:
        self.emit(('AND',))
      elif node.op.token_type == TOK_OR:
        self.emit(('OR',))

    elif isinstance(node, Grouping):
      self.compile(node.value)

    elif isinstance(node, PrintStmt):
      self.compile(node.value)
      if node.end == '':
        self.emit(('PRINT',))
      else:
        self.emit(('PRINTLN',))

    elif isinstance(node, IfStmt):
      self.compile(node.test)
      then_label = self.make_label()
      else_label = self.make_label()
      exit_label = self.make_label()
      self.emit(('JMPZ', else_label))  # Branch directly to else_label if top of stack is EQUAL to ZERO (a.k.a. False)
      self.emit(('LABEL', then_label))
      self.begin_block()
      self.compile(node.then_stmts)
      self.end_block()
      self.emit(('JMP', exit_label))
      self.emit(('LABEL', else_label))
      if node.else_stmts:
        self.begin_block()
        self.compile(node.else_stmts)
        self.end_block()
      self.emit(('LABEL', exit_label))

    elif isinstance(node, WhileStmt):
      test_label = self.make_label()
      body_label = self.make_label()
      exit_label = self.make_label()
      self.emit(('LABEL', test_label))
      self.compile(node.test)
      self.emit(('JMPZ', exit_label))  # Branch directly to exit_label if top of stack is EQUAL to ZERO (a.k.a. False)
      self.emit(('LABEL', body_label))
      self.begin_block()
      self.compile(node.body_stmts)
      self.end_block()
      self.emit(('JMP', test_label))
      self.emit(('LABEL', exit_label))

    elif isinstance(node, ForStmt):
      varname = node.ident.name

      self.begin_block()  # New scope for the loop variable (plus the hidden temporary locals for <end> and <step>)

      # <start> is always a brand-new local, scoped to this loop only (always shadows and never reuses an outer var of the same name)
      self.compile(node.start)
      var_symbol = Symbol(varname, symtype=SYM_VAR, depth=self.scope_depth)
      self.locals.append(var_symbol)
      var_slot = len(self.locals) - 1
      self.emit(('SET_SLOT', f'{var_slot} ({varname})'))

      # <end> becomes a hidden temp local
      self.compile(node.end)
      end_symbol = Symbol('(for-end)', symtype=SYM_VAR, depth=self.scope_depth)
      self.locals.append(end_symbol)
      end_slot = len(self.locals) - 1
      self.emit(('SET_SLOT', f'{end_slot} (for-end)'))

      # <step> becomes a hidden temp local (default: +1)
      if node.step is not None:
        self.compile(node.step)
      else:
        self.emit(('PUSH', (TYPE_NUMBER, +1.0)))
      step_symbol = Symbol('(for-step)', symtype=SYM_VAR, depth=self.scope_depth)
      self.locals.append(step_symbol)
      step_slot = len(self.locals) - 1
      self.emit(('SET_SLOT', f'{step_slot} (for-step)'))

      test_label = self.make_label()
      exit_label = self.make_label()
      self.emit(('LABEL', test_label))

      # We only continue looping if (step >= 0 and i <= end) or (step < 0 and i >= end)

      # Test if (i <= end)
      self.emit(('LOAD_LOCAL', var_slot))
      self.emit(('LOAD_LOCAL', end_slot))
      self.emit(('LE',))  # i <= end

      # Test if (step >= 0)
      self.emit(('LOAD_LOCAL', step_slot))
      self.emit(('PUSH', (TYPE_NUMBER, 0.0)))
      self.emit(('GE',))  # step >= 0
      self.emit(('AND',))

      # Test if (i >= end)
      self.emit(('LOAD_LOCAL', var_slot))
      self.emit(('LOAD_LOCAL', end_slot))
      self.emit(('GE',))  # i >= end

      # Test if (step < 0)
      self.emit(('LOAD_LOCAL', step_slot))
      self.emit(('PUSH', (TYPE_NUMBER, 0.0)))
      self.emit(('LT',))  # step < 0
      self.emit(('AND',))

      # Compare both AND tests from the top of the stack using an OR
      self.emit(('OR',))
      self.emit(('JMPZ', exit_label))

      # Compile and generate the code for the body statements
      self.begin_block()
      self.compile(node.body_stmts)
      self.end_block()

      # Increment the <step>
      self.emit(('LOAD_LOCAL', var_slot))
      self.emit(('LOAD_LOCAL', step_slot))
      self.emit(('ADD',))
      self.emit(('STORE_LOCAL', var_slot))

      # Jump back to the test label
      self.emit(('JMP', test_label))

      self.emit(('LABEL', exit_label))

      self.end_block()  # pops var, end, and step all at once

    elif isinstance(node, Stmts):
      for stmt in node.stmts:
        self.compile(stmt)

    elif isinstance(node, Assignment):
      self.compile(node.right)
      symbol = self.get_var_symbol(node.left.name)
      if not symbol:
        new_symbol = Symbol(node.left.name, symtype=SYM_VAR, depth=self.scope_depth)
        if self.scope_depth == 0:
          self.globals.append(new_symbol)
          new_global_slot = len(self.globals) - 1
          self.emit(('STORE_GLOBAL', new_global_slot))
        else:
          self.locals.append(new_symbol)
          self.emit(('SET_SLOT', str(len(self.locals) - 1) + f" ({new_symbol.name})"))
      else:
        sym, slot = symbol
        if sym.depth == 0:
          self.emit(('STORE_GLOBAL', slot))
        else:
          self.emit(('STORE_LOCAL', slot))

    elif isinstance(node, LocalAssignment):
      if self.scope_depth == 0:
        compile_error(f'"local" cannot be used in the global scope.', node.line)
      self.compile(node.right)
      new_symbol = Symbol(name=node.left.name, symtype=SYM_VAR, depth=self.scope_depth)
      self.locals.append(new_symbol)
      self.emit(('SET_SLOT', str(len(self.locals) - 1) + " (" + str(new_symbol.name) + ")"))

    elif isinstance(node, Identifier):
      symbol = self.get_var_symbol(node.name)
      if not symbol:
        compile_error(f'Variable {node.name} is not defined.', node.line)
      else:
        sym, slot = symbol
        if sym.depth == 0:
          self.emit(('LOAD_GLOBAL', slot))
        else:
          self.emit(('LOAD_LOCAL', slot))

    elif isinstance(node, FuncDecl):
      if self.scope_depth > 0:
        compile_error(f'Functions can only be declared in the global scope. Function {node.name!r} was declared inside a block.', node.line)
      var = self.get_var_symbol(node.name)
      func = self.get_func_symbol(node.name)
      if func:
        compile_error(f'A function with the name {node.name} was already declared.', node.line)
      if var:
        compile_error(f'A variable with the name {node.name} was already defined in this scope.', node.line)
      new_func = Symbol(node.name, symtype=SYM_FUNC, depth=self.scope_depth, arity=len(node.params))
      self.functions.append(new_func)

      end_label = self.make_label()
      self.emit(('JMP', end_label))
      self.emit(('LABEL', new_func.name))
      self.begin_block()
      # Set params as local variables
      for param in node.params:
        new_symbol = Symbol(name=param.name, symtype=SYM_VAR, depth=self.scope_depth)
        self.locals.append(new_symbol)
        self.emit(('SET_SLOT', str(len(self.locals) - 1) + " (" + str(new_symbol.name) + ")"))
      self.compile(node.body_stmts)
      self.end_block()
      self.emit(('PUSH', (TYPE_NUMBER, 0)))
      self.emit(('RTS',))
      self.emit(('LABEL', end_label))

    elif isinstance(node, FuncCall):
      func = self.get_func_symbol(node.name)
      if not func:
        compile_error(f'Not found declaration for function {node.name}', node.line)
      if func.arity != len(node.args):
        compile_error(f'Function expected {func.arity} params but {len(node.args)} args were passed', node.line)
      # Evaluate all args
      for arg in node.args:
        self.compile(arg)
      numargs = (TYPE_NUMBER, len(node.args))
      self.emit(('PUSH', numargs))
      self.emit(('JSR', node.name))

    elif isinstance(node, RetStmt):
      self.compile(node.value)
      self.emit(('RTS',))

    elif isinstance(node, FuncCallStmt):
      self.compile(node.expr)
      self.emit(('POP',)) # <-- Pop the value from the top of the stack, since we are not capturing that return

  def print_code(self):
    i = 0
    for instruction in self.code:
      if instruction[0] == 'LABEL':
        print(f'{i:08} {instruction[1]}:')
        i += 1
        continue
      if instruction[0] == 'PUSH':
        print(f'{i:08}     {instruction[0]} {stringify(instruction[1][1])}')
        i += 1
        continue
      if len(instruction) == 1:
        print(f'{i:08}     {instruction[0]}')
      elif len(instruction) == 2:
        print(f'{i:08}     {instruction[0]} {instruction[1]}')
      i += 1

  def generate_code(self, node):
    self.emit(('LABEL', 'START'))
    self.compile(node)
    self.emit(('HALT',))
    return self.code
