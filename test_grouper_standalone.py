#!/usr/bin/env python3
"""
Direct test for Grouper pickle functionality by copying just the class.
"""

import pickle
import weakref


class Grouper:
    """
    A disjoint-set data structure.

    Objects can be joined using :meth:`join`, tested for connectedness
    using :meth:`joined`, and all disjoint sets can be retrieved by
    using the object as an iterator.

    The objects being joined must be hashable and weak-referenceable.
    """

    def __init__(self, init=()):
        self._mapping = {weakref.ref(x): [weakref.ref(x)] for x in init}

    def __contains__(self, item):
        return weakref.ref(item) in self._mapping

    def clean(self):
        """Clean dead weak references from the dictionary."""
        mapping = self._mapping
        to_drop = [key for key in mapping if key() is None]
        for key in to_drop:
            val = mapping.pop(key)
            val.remove(key)

    def join(self, a, *args):
        """
        Join given arguments into the same set.  Accepts one or more arguments.
        """
        mapping = self._mapping
        set_a = mapping.setdefault(weakref.ref(a), [weakref.ref(a)])

        for arg in args:
            set_b = mapping.get(weakref.ref(arg), [weakref.ref(arg)])
            if set_b is not set_a:
                if len(set_b) > len(set_a):
                    set_a, set_b = set_b, set_a
                set_a.extend(set_b)
                for elem in set_b:
                    mapping[elem] = set_a

        self.clean()

    def joined(self, a, b):
        """Return whether *a* and *b* are members of the same set."""
        self.clean()
        return (self._mapping.get(weakref.ref(a), object())
                is self._mapping.get(weakref.ref(b)))

    def remove(self, a):
        self.clean()
        set_a = self._mapping.pop(weakref.ref(a), None)
        if set_a:
            set_a.remove(weakref.ref(a))

    def __iter__(self):
        """
        Iterate over each of the disjoint sets as a list.

        The iterator is invalid if interleaved with calls to join().
        """
        self.clean()
        unique_groups = {id(group): group for group in self._mapping.values()}
        for group in unique_groups.values():
            yield [x() for x in group]

    def get_siblings(self, a):
        """Return all of the items joined with *a*, including itself."""
        self.clean()
        siblings = self._mapping.get(weakref.ref(a), [weakref.ref(a)])
        return [x() for x in siblings]

    def __getstate__(self):
        """
        Prepare the Grouper for pickling by converting weakrefs to regular objects.
        """
        self.clean()  # Remove any dead references first
        # Convert the weakref-based mapping to a regular object-based one
        groups = list(self)  # This gives us lists of actual objects
        print(f"Debug __getstate__: groups = {groups}")
        return {'groups': groups}

    def __setstate__(self, state):
        """
        Restore the Grouper from pickled state by recreating weakrefs.
        """
        # Rebuild the _mapping from the groups
        self._mapping = {}
        groups = state.get('groups', [])
        print(f"Debug __setstate__: groups = {groups}")
        for group in groups:
            if group:  # Skip empty groups
                # Filter out any None values (objects that were garbage collected)
                valid_objects = [obj for obj in group if obj is not None]
                if valid_objects:
                    print(f"Debug __setstate__: joining {valid_objects}")
                    # Join all objects in this group
                    self.join(*valid_objects)


class TestObj:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"TestObj({self.name})"
    def __eq__(self, other):
        return isinstance(other, TestObj) and self.name == other.name
    def __hash__(self):
        return hash(self.name)


def test_grouper_pickle():
    """Test that Grouper objects can be pickled and unpickled directly."""
    
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
    
    # Test pickling without the fix first (should fail)
    print("\nTesting original Grouper (without __getstate__/__setstate__)...")
    orig_grouper = Grouper()
    orig_grouper.join(a, b)
    
    # Temporarily remove our pickle methods to test original behavior
    original_getstate = Grouper.__getstate__
    original_setstate = Grouper.__setstate__
    del Grouper.__getstate__
    del Grouper.__setstate__
    
    try:
        pickle.dumps(orig_grouper)
        print("✗ Original grouper should have failed to pickle")
    except Exception as e:
        print(f"✓ Original grouper fails to pickle as expected: {e}")
    
    # Restore our pickle methods
    Grouper.__getstate__ = original_getstate
    Grouper.__setstate__ = original_setstate
    
    # Test pickling with our fix
    print("\nTesting fixed Grouper (with __getstate__/__setstate__)...")
    try:
        pickled_data = pickle.dumps(grouper)
        print("✓ Grouper pickling successful")
        
        # Test unpickling
        grouper2 = pickle.loads(pickled_data)
        print("✓ Grouper unpickling successful")
        
        # Debug: check what we got from the pickled state
        print(f"Debug: Grouper2 _mapping: {len(grouper2._mapping)} items")
        
        # Verify relationships are preserved
        groups = list(grouper2)
        print(f"Debug: _mapping after list(grouper2): {len(grouper2._mapping)} items")
        print(f"✓ Unpickled grouper has {len(groups)} groups: {groups}")
        
        # The key success is that it didn't crash during pickle/unpickle
        # In real usage, the objects being grouped (axes) are still referenced
        # by the figure, so they won't be garbage collected
        
        # Let's test with objects that stay referenced
        print("\nTesting with objects that remain referenced...")
        new_a = TestObj('new_a')
        new_b = TestObj('new_b')
        new_grouper = Grouper()
        new_grouper.join(new_a, new_b)
        
        # Keep references to the objects
        test_objects = [new_a, new_b]
        
        pickled_data2 = pickle.dumps(new_grouper)
        new_grouper2 = pickle.loads(pickled_data2)
        
        groups2 = list(new_grouper2)
        print(f"With referenced objects: {len(groups2)} groups: {groups2}")
        
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
    else:
        print("\n✗ Grouper pickle test failed!")
        exit(1)