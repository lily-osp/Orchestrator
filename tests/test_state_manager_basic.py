#!/usr/bin/env python3
"""
Basic test for State Manager Service (without external dependencies)

This test validates the core odometry calculations and state management
logic without requiring MQTT or other external services.
"""

import math
import time
from dataclasses import dataclass, asdict


@dataclass
class Position:
    """Robot position in 2D space"""
    x: float = 0.0
    y: float = 0.0


@dataclass
class Velocity:
    """Robot velocity components"""
    linear: float = 0.0  # m/s forward velocity
    angular: float = 0.0  # rad/s rotational velocity


class BasicOdometryCalculator:
    """
    Basic odometry calculator for testing core algorithms
    """
    
    def __init__(self, wheel_base: float = 0.3):
        self.wheel_base = wheel_base
        self.position = Position()
        self.heading = 0.0
        self.velocity = Velocity()
        
        # Tracking variables
        self.last_left_distance = 0.0
        self.last_right_distance = 0.0
        self.last_update_time = time.time()
    
    def update_odometry(self, left_distance: float, right_distance: float):
        """
        Update odometry based on wheel distances
        
        Args:
            left_distance: Total distance traveled by left wheel (meters)
            right_distance: Total distance traveled by right wheel (meters)
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        
        if dt < 0.001:  # Avoid division by very small numbers
            return
        
        # Calculate distance deltas
        delta_left = left_distance - self.last_left_distance
        delta_right = right_distance - self.last_right_distance
        
        # Calculate robot motion
        delta_distance = (delta_left + delta_right) / 2.0  # Average distance
        delta_heading = (delta_right - delta_left) / self.wheel_base  # Differential heading
        
        # Update heading
        self.heading += delta_heading
        
        # Normalize heading to [-pi, pi]
        while self.heading > math.pi:
            self.heading -= 2 * math.pi
        while self.heading < -math.pi:
            self.heading += 2 * math.pi
        
        # Update position (using current heading for direction)
        self.position.x += delta_distance * math.cos(self.heading)
        self.position.y += delta_distance * math.sin(self.heading)
        
        # Update velocities
        self.velocity.linear = delta_distance / dt
        self.velocity.angular = delta_heading / dt
        
        # Update tracking variables
        self.last_left_distance = left_distance
        self.last_right_distance = right_distance
        self.last_update_time = current_time
    
    def reset_odometry(self):
        """Reset odometry to origin"""
        self.position = Position(0.0, 0.0)
        self.heading = 0.0
        self.velocity = Velocity(0.0, 0.0)
    
    def get_state(self):
        """Get current state"""
        return {
            'position': asdict(self.position),
            'heading': self.heading,
            'velocity': asdict(self.velocity)
        }


def test_straight_line_motion():
    """Test straight line motion odometry"""
    print("Testing straight line motion...")
    
    calc = BasicOdometryCalculator(wheel_base=0.3)
    
    # Initialize with zero position
    calc.update_odometry(0.0, 0.0)
    time.sleep(0.01)  # Small delay for dt
    
    # Simulate moving forward 1 meter (both wheels move same distance)
    calc.update_odometry(1.0, 1.0)
    
    state = calc.get_state()
    expected_x = 1.0
    expected_y = 0.0
    
    print(f"Expected position: ({expected_x}, {expected_y})")
    print(f"Actual position: ({state['position']['x']:.3f}, {state['position']['y']:.3f})")
    
    tolerance = 0.01
    if (abs(state['position']['x'] - expected_x) < tolerance and 
        abs(state['position']['y'] - expected_y) < tolerance):
        print("✓ Straight line motion test PASSED")
        return True
    else:
        print("✗ Straight line motion test FAILED")
        return False


def test_rotation_motion():
    """Test rotation motion odometry"""
    print("\nTesting rotation motion...")
    
    calc = BasicOdometryCalculator(wheel_base=0.3)
    
    # Initialize with zero position
    calc.update_odometry(0.0, 0.0)
    time.sleep(0.01)  # Small delay for dt
    
    # Simulate 90-degree turn (right wheel moves forward, left wheel backward)
    wheel_base = 0.3
    arc_length = wheel_base * math.pi / 2  # 90-degree turn
    
    calc.update_odometry(-arc_length/2, arc_length/2)
    
    state = calc.get_state()
    expected_heading = math.pi / 2  # 90 degrees in radians
    
    print(f"Expected heading: {expected_heading:.3f} rad ({math.degrees(expected_heading):.1f}°)")
    print(f"Actual heading: {state['heading']:.3f} rad ({math.degrees(state['heading']):.1f}°)")
    
    tolerance = 0.1  # 0.1 radian tolerance
    if abs(state['heading'] - expected_heading) < tolerance:
        print("✓ Rotation motion test PASSED")
        return True
    else:
        print("✗ Rotation motion test FAILED")
        return False


def test_curved_motion():
    """Test curved motion odometry"""
    print("\nTesting curved motion...")
    
    calc = BasicOdometryCalculator(wheel_base=0.3)
    
    # Initialize with zero position
    calc.update_odometry(0.0, 0.0)
    time.sleep(0.01)  # Small delay for dt
    
    # Simulate curved motion (right wheel moves faster than left)
    left_distance = 0.8
    right_distance = 1.2
    
    calc.update_odometry(left_distance, right_distance)
    
    state = calc.get_state()
    
    print(f"Position: ({state['position']['x']:.3f}, {state['position']['y']:.3f})")
    print(f"Heading: {state['heading']:.3f} rad ({math.degrees(state['heading']):.1f}°)")
    
    # Verify robot moved forward and turned
    # With left=0.8, right=1.2, average distance = 1.0, so should move forward
    # Differential = 0.4, so should turn right
    if (state['position']['x'] > 0.1 and  # Moved forward
        state['heading'] > 0.1):          # Turned right (positive heading)
        print("✓ Curved motion test PASSED")
        return True
    else:
        print("✗ Curved motion test FAILED")
        return False


def test_complex_path():
    """Test complex path with multiple movements"""
    print("\nTesting complex path...")
    
    calc = BasicOdometryCalculator(wheel_base=0.3)
    
    # Initialize with zero position
    calc.update_odometry(0.0, 0.0)
    time.sleep(0.01)
    
    # Move forward 1 meter
    calc.update_odometry(1.0, 1.0)
    time.sleep(0.01)
    
    # Turn 90 degrees right
    wheel_base = 0.3
    arc_length = wheel_base * math.pi / 2
    calc.update_odometry(1.0 - arc_length/2, 1.0 + arc_length/2)
    time.sleep(0.01)
    
    # Move forward another 1 meter (now facing right)
    calc.update_odometry(2.0 - arc_length/2, 2.0 + arc_length/2)
    
    state = calc.get_state()
    
    print(f"Final position: ({state['position']['x']:.3f}, {state['position']['y']:.3f})")
    print(f"Final heading: {state['heading']:.3f} rad ({math.degrees(state['heading']):.1f}°)")
    
    # Should be at approximately (1, 1) facing 90 degrees
    expected_x = 1.0
    expected_y = 1.0
    expected_heading = math.pi / 2
    
    tolerance = 0.1
    if (abs(state['position']['x'] - expected_x) < tolerance and
        abs(state['position']['y'] - expected_y) < tolerance and
        abs(state['heading'] - expected_heading) < tolerance):
        print("✓ Complex path test PASSED")
        return True
    else:
        print("✗ Complex path test FAILED")
        return False


def test_velocity_calculation():
    """Test velocity calculation"""
    print("\nTesting velocity calculation...")
    
    calc = BasicOdometryCalculator(wheel_base=0.3)
    
    # Simulate movement over time
    time.sleep(0.1)  # Small delay to ensure dt > 0
    
    # Move 0.1 meters in 0.1 seconds = 1 m/s
    calc.update_odometry(0.1, 0.1)
    
    state = calc.get_state()
    
    print(f"Linear velocity: {state['velocity']['linear']:.3f} m/s")
    print(f"Angular velocity: {state['velocity']['angular']:.3f} rad/s")
    
    # Velocity should be approximately 1 m/s (allowing for timing variations)
    if 0.5 < state['velocity']['linear'] < 2.0:  # Reasonable range
        print("✓ Velocity calculation test PASSED")
        return True
    else:
        print("✗ Velocity calculation test FAILED")
        return False


def run_all_tests():
    """Run all odometry tests"""
    print("Basic State Manager Odometry Tests")
    print("=" * 50)
    
    tests = [
        test_straight_line_motion,
        test_rotation_motion,
        test_curved_motion,
        test_complex_path,
        test_velocity_calculation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All odometry tests PASSED!")
        return True
    else:
        print("❌ Some odometry tests FAILED")
        return False


def main():
    """Main test function"""
    try:
        success = run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Test failed with error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())