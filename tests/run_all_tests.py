"""
Test runner - runs all test suites
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_test_suite(test_name, test_functions):
    """Run a test suite and report results"""
    print("\n" + "=" * 70)
    print(f"TEST SUITE: {test_name}")
    print("=" * 70)

    passed = 0
    failed = 0
    errors = []

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_func.__name__, str(e)))
            print(f"\n✗ {test_func.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            errors.append((test_func.__name__, f"Error: {e}"))
            print(f"\n✗ {test_func.__name__} errored: {e}")

    print("\n" + "-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("-" * 70)

    return passed, failed, errors


def main():
    """Run all test suites"""
    print("\n" + "=" * 70)
    print("INGESTION PIPELINE - FULL TEST SUITE")
    print("=" * 70)

    total_passed = 0
    total_failed = 0
    all_errors = []

    # Test Suite 1: Metadata Serialization
    from test_metadata_serialization import (
        test_metadata_serialization_full,
        test_metadata_serialization_minimal,
        test_metadata_serialization_empty_collections
    )

    passed, failed, errors = run_test_suite(
        "Metadata Serialization",
        [
            test_metadata_serialization_full,
            test_metadata_serialization_minimal,
            test_metadata_serialization_empty_collections
        ]
    )
    total_passed += passed
    total_failed += failed
    all_errors.extend(errors)

    # Test Suite 2: LLM Extraction
    from test_llm_extraction import (
        test_llm_extractor_basic,
        test_llm_extractor_with_pdf,
        test_llm_extractor_debug
    )

    passed, failed, errors = run_test_suite(
        "LLM Extraction",
        [
            test_llm_extractor_basic,
            test_llm_extractor_with_pdf,
            test_llm_extractor_debug
        ]
    )
    total_passed += passed
    total_failed += failed
    all_errors.extend(errors)

    # Test Suite 3: Full Pipeline
    from test_pipeline import (
        test_pdf_content_inspection,
        test_full_pipeline,
        test_pipeline_error_handling
    )

    passed, failed, errors = run_test_suite(
        "Full Pipeline",
        [
            test_pdf_content_inspection,
            test_full_pipeline,
            test_pipeline_error_handling
        ]
    )
    total_passed += passed
    total_failed += failed
    all_errors.extend(errors)

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")

    if all_errors:
        print("\nFailed Tests:")
        for test_name, error in all_errors:
            print(f"  - {test_name}: {error}")

    print("=" * 70)

    if total_failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total_failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
