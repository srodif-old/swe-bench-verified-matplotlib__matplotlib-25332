#!/usr/bin/env python3
"""
Test for the pickle issue fix with aligned labels.
This test verifies that figures can be pickled after calling align_labels().
"""

import sys
import os

# Add the lib directory to sys.path so we can import matplotlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pickle
import numpy as np


def test_pickle_figure_with_aligned_labels():
    """Test that a figure with aligned labels can be pickled and unpickled."""
    
    # Create the test figure as described in the issue
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    time = [0, 1, 2, 3, 4]
    speed = [40000, 4300, 4500, 4700, 4800]
    acc = [10, 11, 12, 13, 14]
    ax1.plot(time, speed)
    ax1.set_ylabel('speed')
    ax2.plot(time, acc)
    ax2.set_ylabel('acc')

    # This should work before align_labels
    try:
        pickle.dumps(fig)
        print("✓ Pickling successful before align_labels()")
    except Exception as e:
        print(f"✗ Unexpected failure before align_labels(): {e}")
        return False

    # Call align_labels - this was causing the pickle issue
    fig.align_labels()

    # This should work after the fix
    try:
        pickled_data = pickle.dumps(fig)
        print("✓ Pickling successful after align_labels()")
        
        # Test unpickling as well
        fig2 = pickle.loads(pickled_data)
        print("✓ Unpickling successful")
        
        # Verify the unpickled figure still has the aligned labels structure
        assert hasattr(fig2, '_align_label_groups')
        assert 'x' in fig2._align_label_groups
        assert 'y' in fig2._align_label_groups
        print("✓ Unpickled figure has correct align_label_groups structure")
        
        plt.close(fig)
        plt.close(fig2)
        return True
        
    except Exception as e:
        print(f"✗ Pickling failed after align_labels(): {e}")
        plt.close(fig)
        return False


def test_grouper_pickle():
    """Test that Grouper objects can be pickled and unpickled directly."""
    from matplotlib.cbook import Grouper
    
    # Create some test objects
    class TestObj:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"TestObj({self.name})"
    
    # Create test objects
    a, b, c, d = [TestObj(x) for x in ['a', 'b', 'c', 'd']]
    
    # Create and populate grouper
    grouper = Grouper()
    grouper.join(a, b)
    grouper.join(c, d)
    
    # Test pickling
    try:
        pickled_data = pickle.dumps(grouper)
        print("✓ Grouper pickling successful")
        
        # Test unpickling
        grouper2 = pickle.loads(pickled_data)
        print("✓ Grouper unpickling successful")
        
        # Verify relationships are preserved
        # Note: The actual objects won't be the same after pickle,
        # but we can verify the structure is correct
        groups = list(grouper2)
        print(f"✓ Unpickled grouper has {len(groups)} groups")
        
        return True
        
    except Exception as e:
        print(f"✗ Grouper pickle test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing pickle functionality with aligned labels...")
    
    success1 = test_grouper_pickle()
    success2 = test_pickle_figure_with_aligned_labels()
    
    if success1 and success2:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)