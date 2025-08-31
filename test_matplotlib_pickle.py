#!/usr/bin/env python3
"""
Test to verify that the pickle fix for Grouper works with matplotlib-like objects.
This test simulates the actual matplotlib usage pattern where axes objects remain
referenced by a figure object.
"""

import pickle


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
        # Import our fixed Grouper directly
        import sys
        import os
        import importlib.util
        
        # Mock the dependencies for cbook
        sys.modules["numpy"] = type('MockNumpy', (), {})()
        sys.modules["matplotlib"] = type('MockMatplotlib', (), {})()
        sys.modules["matplotlib._api"] = type('MockAPI', (), {})()
        sys.modules["matplotlib._c_internal_utils"] = type('MockCInternal', (), {})()
        
        spec = importlib.util.spec_from_file_location("cbook", 
            os.path.join(os.path.dirname(__file__), 'lib', 'matplotlib', 'cbook.py'))
        cbook = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cbook)
        
        Grouper = cbook.Grouper
        
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


if __name__ == "__main__":
    success = test_matplotlib_style_pickle()
    
    if success:
        print("\n✓ Matplotlib-style pickle test passed!")
    else:
        print("\n✗ Matplotlib-style pickle test failed!")
        exit(1)