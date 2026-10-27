from defs import *
from utils import *
from model import *
from tokens import *
from state import *
import codecs

class Interpreter:
  def __init__(self, ):
    self.built_in_funcs = {
      "len": self.len,
      "push": self.push,
      "pop": self.pop
    }

  # Extended: built-in len
  def len(self, args):
    valtype, value = args[0]
    return (TYPE_NUMBER, len(value))

  # Extended: built-in push
  def push(self, args):
    _, array = args[0]
    eltype, element = args[1]
    array.append((eltype, element))
    return (TYPE_NUMBER, len(array)) # return the new length

  # Extended: built-in pop
  def pop(self, args):
    _, array = args[0]
    return array.pop()

  def interpret(self, node, env):
    if isinstance(node, Integer):
      return (TYPE_NUMBER, int(node.value))

    elif isinstance(node, Float):
      return (TYPE_NUMBER, float(node.value))

    elif isinstance(node, String):
      return (TYPE_STRING, str(node.value))

    elif isinstance(node, Bool):
      return (TYPE_BOOL, node.value)

    elif isinstance(node, Grouping):
      return self.interpret(node.value, env)

    elif isinstance(node, Array):
      values = []
      for value in node.values:
        values.append(self.interpret(value, env))
      return (TYPE_ARRAY, values)

    # Extended: MemberExpr
    elif isinstance(node, MemberExpr):
      objtype, obj = self.interpret(node.obj, env)
      if node.computed:
        proptype, prop = self.interpret(node.prop, env)
        if objtype == TYPE_STRING:
          return (TYPE_STRING, obj[prop])
        return obj[prop]

    elif isinstance(node, Identifier):
      value = env.get_var(node.name)
      if value is None:
        runtime_error(f'Undeclared identifier {node.name!r}', node.line)
      if value[1] is None:
        runtime_error(f'Uninitialized identifier {node.name!r}', node.line)
      return value

    elif isinstance(node, Assignment):
      # Evaluate the right-hand side expression
      righttype, rightval = self.interpret(node.right, env)

      # Extended: assign value of member expr
      if isinstance(node.left, MemberExpr):
        typeobj, obj = self.interpret(node.left.obj, env)
        if node.left.computed:
          typeprop, prop = self.interpret(node.left.prop, env)
          obj[prop] = (righttype, rightval)
      else:
        # Update the value of the left-hand side variable or create a new one
        env.set_var(node.left.name, (righttype, rightval))

    elif isinstance(node, LocalAssignment):
      if env.parent is None:
        runtime_error(f'"local" cannot be used in the global scope.', node.line)
      # Evaluate the right-hand side expression
      righttype, rightval = self.interpret(node.right, env)
      # Always create a new variable in the current scope/environment
      env.set_local(node.left.name, (righttype, rightval))

    elif isinstance(node, BinOp):
      lefttype, leftval  = self.interpret(node.left, env)
      righttype, rightval = self.interpret(node.right, env)
      if node.op.token_type == TOK_PLUS:
        if lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER:
          return (TYPE_NUMBER, leftval + rightval)
        elif lefttype == TYPE_STRING or righttype == TYPE_STRING:
          return (TYPE_STRING, stringify(leftval) + stringify(rightval))
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_MINUS:
        if lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER:
          return (TYPE_NUMBER, leftval - rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_STAR:
        if lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER:
          return (TYPE_NUMBER, leftval * rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_SLASH:
        if rightval == 0:
          runtime_error(f'Division by zero.', node.line)
        if lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER:
          return (TYPE_NUMBER, leftval / rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_MOD:
        if lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER:
          return (TYPE_NUMBER, leftval % rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_CARET:
        if lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER:
          return (TYPE_NUMBER, leftval ** rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_GT:
        if (lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER) or (lefttype == TYPE_STRING and righttype == TYPE_STRING):
          return (TYPE_BOOL, leftval > rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_GE:
        if (lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER) or (lefttype == TYPE_STRING and righttype == TYPE_STRING):
          return (TYPE_BOOL, leftval >= rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_LT:
        if (lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER) or (lefttype == TYPE_STRING and righttype == TYPE_STRING):
          return (TYPE_BOOL, leftval < rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_LE:
        if (lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER) or (lefttype == TYPE_STRING and righttype == TYPE_STRING):
          return (TYPE_BOOL, leftval <= rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_EQEQ:
        if (lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER) or (lefttype == TYPE_STRING and righttype == TYPE_STRING) or (lefttype == TYPE_BOOL and righttype == TYPE_BOOL):
          return (TYPE_BOOL, leftval == rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

      elif node.op.token_type == TOK_NE:
        if (lefttype == TYPE_NUMBER and righttype == TYPE_NUMBER) or (lefttype == TYPE_STRING and righttype == TYPE_STRING) or (lefttype == TYPE_BOOL and righttype == TYPE_BOOL):
          return (TYPE_BOOL, leftval != rightval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} between {lefttype} and {righttype}.', node.op.line)

    elif isinstance(node, UnOp):
      operandtype, operandval = self.interpret(node.operand, env)
      if node.op.token_type == TOK_MINUS:
        if operandtype == TYPE_NUMBER:
          return (TYPE_NUMBER, -operandval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} with {operandtype}.', node.op.line)

      if node.op.token_type == TOK_PLUS:
        if operandtype == TYPE_NUMBER:
          return (TYPE_NUMBER, operandval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} with {operandtype}.', node.op.line)

      elif node.op.token_type == TOK_NOT:
        if operandtype == TYPE_BOOL:
          return (TYPE_BOOL, not operandval)
        else:
          runtime_error(f'Unsupported operator {node.op.lexeme!r} with {operandtype}.', node.op.line)

    elif isinstance(node, LogicalOp):
      lefttype, leftval = self.interpret(node.left, env)
      if node.op.token_type == TOK_OR:
        if leftval:
          return (lefttype, leftval)
      elif node.op.token_type == TOK_AND:
        if not leftval:
          return (lefttype, leftval)
      return self.interpret(node.right, env)

    elif isinstance(node, Stmts):
      #Evaluate statements in sequence, one after the other.
      for stmt in node.stmts:
        self.interpret(stmt, env)

    elif isinstance(node, PrintStmt):
      exprtype, exprval = self.interpret(node.value, env)
      if exprtype == TYPE_ARRAY:
        print('[' + ', '.join('[Array('+ str(len(value)) + ')]' if t == TYPE_ARRAY else str(value) for t, value in exprval) + ']')
      else:
        val = stringify(exprval)
        print(codecs.escape_decode(bytes(val, "utf-8"))[0].decode("utf-8"), end=node.end)

    elif isinstance(node, IfStmt):
      testtype, testval = self.interpret(node.test, env)
      if testtype != TYPE_BOOL:
        runtime_error("Condition test is not a boolean expression.", node.line)
      if testval:
        self.interpret(node.then_stmts, env.new_env()) # We must create a new child scope for the then-block
      else:
        self.interpret(node.else_stmts, env.new_env()) # We must create a new child scope for the else-block

    elif isinstance(node, WhileStmt):
      new_env = env.new_env()
      while True:
        testtype, testval = self.interpret(node.test, env)
        if testtype != TYPE_BOOL:
          runtime_error(f'While test is not a boolean expression.', node.line)
        if not testval:
          break
        self.interpret(node.body_stmts, new_env) # pass the new child environment for the scope of the while block

    elif isinstance(node, ForStmt):
      varname = node.ident.name
      itype, i = self.interpret(node.start, env)
      endtype, end = self.interpret(node.end, env)
      block_new_env = env.new_env()
      if node.step is None:
        step = +1
      else:
        steptype, step = self.interpret(node.step, env)
      while (step >= 0 and i <= end) or (step < 0 and i >= end):
        newval = (TYPE_NUMBER, i)
        block_new_env.set_local(varname, newval)
        self.interpret(node.body_stmts, block_new_env) # pass the new child environment for the scope of the while block
        i = i + step

    elif isinstance(node, FuncDecl):
      if env.parent is not None:
        runtime_error(f'Functions can only be declared in the global scope. Function {node.name!r} was declared inside a block.', node.line)
      env.set_func(node.name, (node, env)) # we also store the environment in which the function was declared

    elif isinstance(node, FuncCall):
      # Extended: built-in functions
      if node.name in self.built_in_funcs:
        args = []
        for arg in node.args:
          args.append(self.interpret(arg, env))
        return self.built_in_funcs[node.name](args)

      # We must make sure the function was declared
      func = env.get_func(node.name)

      if not func:
        runtime_error(f'Function {node.name!r} not declared.', node.line)

      # Fetch the function declaration
      func_decl = func[0] #--> get the function declaration node that was saved in the environment
      func_env  = func[1] #--> get the environment in which the function was originally declared

      # Does the number of args match the expected number of params
      if len(node.args) != len(func_decl.params):
        runtime_error(f'Function {func_decl.name!r} expected {len(func_decl.params)} params but {len(node.args)} args were passed.', node.line)

      # We need to evaluate all the args
      args = []
      for arg in node.args:
        args.append(self.interpret(arg, env))

      # Create a new nested block environment for the function
      new_func_env = func_env.new_env()

      # We must create local variables in the new child environment of the function for the parameters and bind the argument values to them!
      for param, argval in zip(func_decl.params, args):
        new_func_env.set_local(param.name, argval)

      # Finally, we ask to interpret the body_stmts of the function declaration
      try:
        self.interpret(func_decl.body_stmts, new_func_env)
        return (TYPE_NUMBER, 0)
      except Return as e:
        return e.args[0] # <-- args is the arguments passed to the exception

    elif isinstance(node, FuncCallStmt):
      self.interpret(node.expr, env)

    elif isinstance(node, RetStmt):
      raise Return(self.interpret(node.value, env))

  def interpret_ast(self, node):
    # Entry point of our interpreter creating a brand new global/parent environment
    env = Environment()
    self.interpret(node, env)


class Return(Exception):
  pass
