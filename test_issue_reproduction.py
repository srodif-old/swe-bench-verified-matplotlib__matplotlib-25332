#!/usr/bin/env python3
"""
Test to verify that the pickle fix for Grouper works with matplotlib-like objects.
This test simulates the actual matplotlib usage pattern where axes objects remain
referenced by a figure object.
"""

import pickle
import weakref


# Copy the fixed Grouper class directly here for testing
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
        return {'groups': groups}

    def __setstate__(self, state):
        """
        Restore the Grouper from pickled state by recreating weakrefs.
        """
        # Rebuild the _mapping from the groups
        self._mapping = {}
        groups = state.get('groups', [])
        for group in groups:
            if group:  # Skip empty groups
                # Filter out any None values (objects that were garbage collected)
                valid_objects = [obj for obj in group if obj is not None]
                if valid_objects:
                    # Join all objects in this group
                    self.join(*valid_objects)


class MockAxis:
    """Mock axis object that simulates matplotlib Axes behavior."""
    
    def __init__(self, name):
        self.name = name
        self._subplotspec = MockSubplotSpec()
    
    def get_subplotspec(self):
        return self._subplotspec
    
    def __repr__(self):
        return f"MockAxis({self.name})"
    
    def __hash__(self):
        return hash(self.name)


class MockSubplotSpec:
    """Mock subplot spec."""
    
    def __init__(self):
        pass


class MockFigure:
    """Mock figure that holds axes and grouper objects like matplotlib."""
    
    def __init__(self):
        self.axes = []
        self._align_label_groups = {"x": Grouper(), "y": Grouper()}
    
    def add_subplot(self, name):
        ax = MockAxis(name)
        self.axes.append(ax)
        return ax
    
    def align_labels(self):
        """Simulate matplotlib's align_labels functionality."""
        # Get axes with subplot specs
        axs = [ax for ax in self.axes if ax.get_subplotspec() is not None]
        
        # Join some axes for testing
        if len(axs) >= 2:
            self._align_label_groups['x'].join(axs[0], axs[1])
        if len(axs) >= 4:
            self._align_label_groups['y'].join(axs[2], axs[3])


def test_matplotlib_style_pickle():
    """Test pickle with matplotlib-style object relationships."""
    
    print("Testing matplotlib-style pickle with Grouper fix...")
    
    # Create a mock figure
    fig = MockFigure()
    
    # Add some axes
    ax1 = fig.add_subplot("ax1")
    ax2 = fig.add_subplot("ax2")
    ax3 = fig.add_subplot("ax3")
    ax4 = fig.add_subplot("ax4")
    
    print(f"Created figure with {len(fig.axes)} axes")
    
    # Test pickling before align_labels (should work)
    try:
        pickle.dumps(fig)
        print("✓ Pickling successful before align_labels()")
    except Exception as e:
        print(f"✗ Unexpected failure before align_labels(): {e}")
        return False
    
    # Call align_labels which uses the Grouper
    fig.align_labels()
    print("Called align_labels()")
    
    # Check that groupers have content
    x_groups = list(fig._align_label_groups['x'])
    y_groups = list(fig._align_label_groups['y'])
    print(f"X grouper has {len(x_groups)} groups: {x_groups}")
    print(f"Y grouper has {len(y_groups)} groups: {y_groups}")
    
    # Test pickling after align_labels (this was failing before the fix)
    try:
        pickled_data = pickle.dumps(fig)
        print("✓ Pickling successful after align_labels()")
        
        # Test unpickling
        fig2 = pickle.loads(pickled_data)
        print("✓ Unpickling successful")
        
        # Verify structure is preserved
        assert len(fig2.axes) == len(fig.axes)
        assert hasattr(fig2, '_align_label_groups')
        assert 'x' in fig2._align_label_groups
        assert 'y' in fig2._align_label_groups
        
        print("✓ Unpickled figure has correct structure")
        print(f"✓ Unpickled figure has {len(fig2.axes)} axes")
        
        # The groupers in the unpickled figure should work with their new axes
        x_groups2 = list(fig2._align_label_groups['x'])
        y_groups2 = list(fig2._align_label_groups['y'])
        print(f"Unpickled X grouper has {len(x_groups2)} groups: {x_groups2}")
        print(f"Unpickled Y grouper has {len(y_groups2)} groups: {y_groups2}")
        
        return True
        
    except Exception as e:
        print(f"✗ Pickling failed after align_labels(): {e}")
        import traceback
        traceback.print_exc()
        return False


def test_original_issue():
    """Test the original issue reproduction with our fix."""
    print("\nTesting original issue reproduction...")
    
    class MockPlot:
        """Mock figure and axes to simulate the original issue."""
        def __init__(self):
            self.fig = MockFigure()
            
        def setup_plot(self):
            ax1 = self.fig.add_subplot('ax1')
            ax2 = self.fig.add_subplot('ax2')
            
            # Simulate setting labels and plotting  
            ax1.ylabel = 'speed'
            ax2.ylabel = 'acc'
            
            return ax1, ax2
    
    plot = MockPlot()
    ax1, ax2 = plot.setup_plot()
    
    print("Before align_labels() - trying to pickle...")
    try:
        pickle.dumps(plot.fig)
        print("✓ Pickling successful before align_labels()")
    except Exception as e:
        print(f"✗ Pickling failed before align_labels(): {e}")
        return False

    plot.fig.align_labels() # This was causing the issue
    
    print("After align_labels() - trying to pickle...")
    try:
        pickled_data = pickle.dumps(plot.fig)
        print("✓ Pickling successful after align_labels() - ISSUE FIXED!")
        
        # Test unpickling as well
        fig2 = pickle.loads(pickled_data)
        print("✓ Unpickling successful")
        return True
        
    except Exception as e:
        print(f"✗ Pickling failed after align_labels(): {e}")
        return False


if __name__ == "__main__":
    success1 = test_matplotlib_style_pickle()
    success2 = test_original_issue()
    
    if success1 and success2:
        print("\n✓ All tests passed! The fix works correctly.")
    else:
        print("\n✗ Some tests failed!")
        exit(1)