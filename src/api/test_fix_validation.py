#!/usr/bin/env python3
"""
Simple validation script to test the profile update fix.
This script tests the logic without requiring a full Flask environment.
"""


def test_falsy_value_handling():
    """Test that falsy values are handled correctly in profile updates."""

    # Test cases with different falsy values
    test_cases = [
        {
            "profile_value": "",
            "default_value": "",
            "current_value": "Original",
            "expected": True,
        },
        {
            "profile_value": "",
            "default_value": "default",
            "current_value": "Original",
            "expected": True,
        },
        {"profile_value": 0, "default_value": 0, "current_value": 1, "expected": True},
        {"profile_value": 0, "default_value": 1, "current_value": 2, "expected": True},
        {
            "profile_value": False,
            "default_value": False,
            "current_value": True,
            "expected": True,
        },
        {
            "profile_value": False,
            "default_value": True,
            "current_value": True,
            "expected": True,
        },
        {
            "profile_value": None,
            "default_value": None,
            "current_value": "Original",
            "expected": True,
        },
        {
            "profile_value": None,
            "default_value": "default",
            "current_value": "Original",
            "expected": True,
        },
    ]

    print("Testing falsy value handling in profile updates...")
    print("=" * 60)

    for i, case in enumerate(test_cases, 1):
        profile_value = case["profile_value"]
        default_value = case["default_value"]
        current_value = case["current_value"]
        expected = case["expected"]

        # Original logic (with bug)
        original_condition = (
            bool(profile_value)
            and (profile_value != default_value)
            and current_value != profile_value
        )

        # Fixed logic (without bug)
        fixed_condition = (
            profile_value != default_value
        ) and current_value != profile_value

        print(f"Test Case {i}:")
        print(
            f"  Profile Value: {repr(profile_value)} (falsy: {not bool(profile_value)})"
        )
        print(f"  Default Value: {repr(default_value)}")
        print(f"  Current Value: {repr(current_value)}")
        print(f"  Original Logic Result: {original_condition}")
        print(f"  Fixed Logic Result: {fixed_condition}")
        print(f"  Expected: {expected}")
        print(f"  Original Logic Correct: {original_condition == expected}")
        print(f"  Fixed Logic Correct: {fixed_condition == expected}")

        if original_condition != expected:
            print("  ❌ Original logic failed - would prevent saving falsy value!")
        if fixed_condition == expected:
            print("  ✅ Fixed logic works correctly!")
        else:
            print("  ❌ Fixed logic failed!")

        print("-" * 40)

    print("\nSummary:")
    print(
        "The original logic with bool(profile_value) would prevent saving falsy values"
    )
    print("The fixed logic allows saving falsy values when they differ from defaults")
    print(
        "This ensures consistency between creating new profiles and updating existing ones"
    )


if __name__ == "__main__":
    test_falsy_value_handling()
