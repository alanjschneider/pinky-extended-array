class Environment:
  def __init__(self, parent=None):
    self.vars = {}       # A dictionary to store variable names and their values
    self.funcs = {}      # A dictionary to store the functions
    self.parent = parent # Parent environemt (optional)

  def get_var(self, name):
    '''
    Search the current environment and all parent environments for a variable name (return None if we dont find any)
    '''
    while self:
      value = self.vars.get(name)
      if value is not None:
        return value
      else:
        self = self.parent # Look in parent environments to see if variable is defined "above"
    return None

  def set_var(self, name, value):
    '''
    Store a value in the environment (dynamically updating an existing name or creating a new entry in the dictionary)
    '''
    original_env = self
    while self:
      if name in self.vars:
        self.vars[name] = value
        return value
      self = self.parent
    # If we did not find the variable in the environments above, we create it in the original one
    original_env.vars[name] = value

  def set_local(self, name, value):
    self.vars[name] = value

  def get_func(self, name):
    '''
    Searches the current environment and all parent environments for a function name (returns None if it does not find any)
    '''
    while self:
      value = self.funcs.get(name)
      if value is not None:
        return value
      else:
        self = self.parent # Look in parent environments to see if the function is defined "above"
    return None

  def set_func(self, name, value):
    '''
    Declares a function (also stores the environment in which it was declared)
    '''
    self.funcs[name] = value

  def new_env(self):
    '''
    Return a new environment that is a child of the current one.
    This is used to create a new nested scope (while, funcs, etc.)
    '''
    return Environment(parent=self)
