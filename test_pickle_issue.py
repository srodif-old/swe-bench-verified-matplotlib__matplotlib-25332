#!/usr/bin/env python3
"""
Test script to reproduce the pickle issue with aligned labels.
"""

import matplotlib.pyplot as plt
import pickle

# Reproduce the issue
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)
time=[0,1,2,3,4]
speed=[40000,4300,4500,4700,4800]
acc=[10,11,12,13,14]
ax1.plot(time,speed)
ax1.set_ylabel('speed')
ax2.plot(time,acc)
ax2.set_ylabel('acc')

print("Before align_labels() - trying to pickle...")
try:
    pickle.dumps(fig)
    print("✓ Pickling successful before align_labels()")
except Exception as e:
    print(f"✗ Pickling failed before align_labels(): {e}")

fig.align_labels() # pickling works after removing this line 

print("After align_labels() - trying to pickle...")
try:
    pickle.dumps(fig)
    print("✓ Pickling successful after align_labels()")
except Exception as e:
    print(f"✗ Pickling failed after align_labels(): {e}")

plt.close(fig)