#!/usr/bin/env python3
"""
Simple test for Grouper pickle functionality without matplotlib dependencies.
"""

import sys
import os
import pickle

# Add the lib directory to sys.path so we can import the cbook module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

try:
    from matplotlib.cbook import Grouper
except ImportError as e:
    print(f"Could not import Grouper: {e}")
    # Let's try to test the specific methods directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("cbook", os.path.join(os.path.dirname(__file__), 'lib', 'matplotlib', 'cbook.py'))
    cbook = importlib.util.module_from_spec(spec)
    sys.modules["cbook"] = cbook
    
    # We need to provide the required imports for cbook.py
    sys.modules["numpy"] = type('MockNumpy', (), {})()  # Mock numpy
    sys.modules["matplotlib"] = type('MockMatplotlib', (), {})()  # Mock matplotlib
    sys.modules["matplotlib._api"] = type('MockAPI', (), {})()  # Mock _api
    sys.modules["matplotlib._c_internal_utils"] = type('MockCInternal', (), {})()  # Mock _c_internal_utils
    
    try:
        spec.loader.exec_module(cbook)
        Grouper = cbook.Grouper
        print("Successfully imported Grouper from cbook module")
    except Exception as e:
        print(f"Failed to load cbook module: {e}")
        sys.exit(1)


def test_grouper_pickle():
    """Test that Grouper objects can be pickled and unpickled directly."""
    
    # Create some test objects that are hashable and weak-referenceable
    class TestObj:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"TestObj({self.name})"
        def __eq__(self, other):
            return isinstance(other, TestObj) and self.name == other.name
        def __hash__(self):
            return hash(self.name)
    
    # Create test objects
    a = TestObj('a')
    b = TestObj('b') 
    c = TestObj('c')
    d = TestObj('d')
    
    print("Testing Grouper pickle functionality...")
    
    # Create and populate grouper
    grouper = Grouper()
    print(f"Created empty grouper: {list(grouper)}")
    
    grouper.join(a, b)
    grouper.join(c, d)
    print(f"After joining: {list(grouper)}")
    
    # Test that original grouper works
    assert grouper.joined(a, b), "a and b should be joined"
    assert grouper.joined(c, d), "c and d should be joined"
    assert not grouper.joined(a, c), "a and c should not be joined"
    print("✓ Original grouper works correctly")
    
    # Test pickling
    try:
        pickled_data = pickle.dumps(grouper)
        print("✓ Grouper pickling successful")
        
        # Test unpickling
        grouper2 = pickle.loads(pickled_data)
        print("✓ Grouper unpickling successful")
        
        # Check that we can add new items to the unpickled grouper
        e = TestObj('e')
        grouper2.join(a, e)  # This should work if 'a' still exists in grouper2
        
        groups = list(grouper2)
        print(f"✓ Unpickled grouper has {len(groups)} groups: {groups}")
        
        return True
        
    except Exception as e:
        print(f"✗ Grouper pickle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_grouper_pickle()
    
    if success:
        print("\n✓ Grouper pickle test passed!")
        sys.exit(0)
    else:
        print("\n✗ Grouper pickle test failed!")
        sys.exit(1)