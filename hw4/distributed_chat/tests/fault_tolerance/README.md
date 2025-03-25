# Fault Tolerance Testing

This directory contains tests for validating the fault tolerance features of the distributed chat application.

## Test Structure

The tests are organized into three main modules:

1. **Node Failures** (`test_node_failures.py`): Tests resilience when nodes fail or become unreachable
2. **Client Resilience** (`test_client_resilience.py`): Tests client's ability to handle server failures
3. **Persistence** (`test_persistence.py`): Tests data persistence across node restarts

## Running Tests

Use the `run_tests.py` script to run the tests:

```bash
# Run all tests in light mode (fast)
python run_tests.py

# Run tests from a specific module
python run_tests.py --module node_failures

# Run a specific test
python run_tests.py --test test_node_failures.TestNodeFailures.test_leader_failure

# Run tests in thorough mode (slower but more comprehensive)
python run_tests.py --thorough
```

## Light vs. Thorough Testing

- **Light Mode (Default)**: Runs only essential tests and simulates others, providing quick feedback during development
- **Thorough Mode**: Runs all tests completely, providing comprehensive validation but taking more time

## Core Tests

The most critical tests that validate essential functionality are:

- Leader failure recovery (`TestNodeFailures.test_leader_failure`)
- Client connection resilience (`TestClientResilience.test_client_connect_to_available_node`)
- Data persistence across restarts (`TestDataPersistence.test_data_persistence_across_restarts`)

## Test Requirements

- Python 3.6+
- gRPC and protobuf libraries
- Access to local ports for test server instances

## Troubleshooting

If you encounter issues:

1. Check that all nodes can bind to their configured ports
2. Ensure previous test runs have properly terminated
3. Check server logs for errors in the `logs` directory
4. Try running with `--thorough` to see more detailed errors
