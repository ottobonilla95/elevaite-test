"""Security tests for sandbox escape prevention.

These tests verify that various known Python sandbox escape techniques are blocked.
"""

from code_execution_service.services.validator import CodeValidator


class TestSandboxEscapes:
    """Tests for preventing common sandbox escape techniques."""

    def test_escape_via_class_mro(self, validator: CodeValidator):
        """Test blocking of __mro__ access for class hierarchy traversal."""
        code = """
# Attempt to access builtins via MRO
x = ''.__class__.__mro__[1].__subclasses__()
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_globals(self, validator: CodeValidator):
        """Test blocking of __globals__ for accessing global namespace."""
        code = """
# Attempt to access globals via function
def f(): pass
f.__globals__['__builtins__']
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_code_object(self, validator: CodeValidator):
        """Test blocking of __code__ attribute access."""
        code = """
# Attempt to access code object
def f(): pass
f.__code__
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_import_function(self, validator: CodeValidator):
        """Test blocking of __import__ builtin."""
        code = """
# Attempt to import using __import__
os = __import__('os')
os.system('ls')
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_builtins(self, validator: CodeValidator):
        """Test blocking of __builtins__ access."""
        code = """
# Attempt to access builtins directly
__builtins__['eval']('1+1')
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_getattr(self, validator: CodeValidator):
        """Test blocking of getattr for dynamic attribute access."""
        code = """
# Attempt to use getattr for evasion
getattr(getattr('', '__class__'), '__bases__')
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_type_call(self, validator: CodeValidator):
        """Test blocking of type() for introspection."""
        code = """
# Attempt to use type for introspection
t = type('Exploit', (), {'run': lambda: __import__('os')})
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_bases(self, validator: CodeValidator):
        """Test blocking of __bases__ for class hierarchy access."""
        code = """
# Attempt to traverse class hierarchy
class X: pass
X.__bases__[0].__subclasses__()
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_loader(self, validator: CodeValidator):
        """Test blocking of __loader__ access."""
        code = """
# Attempt to access module loader
import json
json.__loader__
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_spec(self, validator: CodeValidator):
        """Test blocking of __spec__ access."""
        code = """
# Attempt to access module spec
import json
json.__spec__
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_dict(self, validator: CodeValidator):
        """Test blocking of __dict__ for object introspection."""
        code = """
# Attempt to access class dict
class X: secret = 'password'
X.__dict__
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_via_compile(self, validator: CodeValidator):
        """Test blocking of compile() for dynamic code compilation."""
        code = """
# Attempt to compile and exec arbitrary code
code = compile('import os; os.system("ls")', '<string>', 'exec')
exec(code)
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_escape_nested_import_attempt(self, validator: CodeValidator):
        """Test blocking nested import attempts."""
        code = """
# Attempt nested evasion
x = ().__class__.__bases__[0].__subclasses__()[40]('/etc/passwd').read()
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_pickle_deserialization_attack(self, validator: CodeValidator):
        """Test blocking of pickle for potential RCE."""
        code = """
import pickle
# Pickle can execute arbitrary code during deserialization
"""
        result = validator.validate(code)
        assert not result.is_valid

    def test_ctypes_bypass(self, validator: CodeValidator):
        """Test blocking of ctypes for native code execution."""
        code = """
import ctypes
# ctypes allows calling arbitrary native functions
"""
        result = validator.validate(code)
        assert not result.is_valid
