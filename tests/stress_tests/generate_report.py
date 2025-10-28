import sys
import json
import os
from collections import Counter

def calculate_percentiles(data, percentiles_to_calc):
    """Calculates the given percentiles for a list of numbers."""
    if not data:
        return {p: "N/A" for p in percentiles_to_calc}

    data.sort()
    results = {}
    for p in percentiles_to_calc:
        index = int(p / 100 * (len(data) - 1))
        results[p] = data[index]
    return results

def analyze_log_file(log_file_path):
    """
    Reads a log file, aggregates data, and returns a dictionary of calculated metrics.
    """
    latencies = []
    status_codes = Counter()
    outcomes = Counter()
    errors = []
    run_id = "unknown"
    total_requests = 0

    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at '{log_file_path}'")
        sys.exit(1)

    with open(log_file_path, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)

                # Capture the run_id from the first valid entry
                if run_id == "unknown" and 'details' in log_entry and 'run_id' in log_entry['details']:
                    run_id = log_entry['details']['run_id']

                # We only care about API stresser logs for this report
                if log_entry.get('name') == 'api_stresser' and log_entry.get('message') == 'API request completed':
                    details = log_entry.get('details', {})
                    total_requests += 1

                    if 'latency_ms' in details:
                        latencies.append(details['latency_ms'])

                    if 'status_code' in details:
                        status_codes[details['status_code']] += 1

                    if 'outcome' in details:
                        outcomes[details['outcome']] += 1
                        # Collect critical error messages
                        if details['outcome'] == 'failure' or details['outcome'] == 'connection_error':
                            if len(errors) < 20: # Limit to the first 20 errors
                                errors.append(log_entry)

            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from line: {line.strip()}")
                continue

    # --- Calculate Metrics ---
    total_failures = outcomes.get('failure', 0) + outcomes.get('connection_error', 0)
    success_rate = ((total_requests - total_failures) / total_requests * 100) if total_requests > 0 else 100

    latency_stats = {}
    if latencies:
        latency_stats['min_ms'] = min(latencies)
        latency_stats['max_ms'] = max(latencies)
        latency_stats['average_ms'] = sum(latencies) / len(latencies)
        percentiles = calculate_percentiles(latencies, [50, 90, 95, 99])
        latency_stats['p50_ms (Median)'] = percentiles[50]
        latency_stats['p90_ms'] = percentiles[90]
        latency_stats['p95_ms'] = percentiles[95]
        latency_stats['p99_ms'] = percentiles[99]

    status_code_dist = {str(code): count for code, count in status_codes.items()}

    return {
        "run_id": run_id,
        "total_requests": total_requests,
        "total_failures": total_failures,
        "success_rate_percent": success_rate,
        "latency_stats": latency_stats,
        "status_code_distribution": status_code_dist,
        "outcome_summary": dict(outcomes),
        "critical_errors": errors
    }

def generate_markdown_report(metrics, output_file_path):
    """
    Writes the calculated metrics to a human-readable Markdown file.
    """
    with open(output_file_path, 'w') as f:
        f.write(f"# Stress Test Performance Report\n\n")
        f.write(f"**Run ID:** `{metrics['run_id']}`\n\n")
        f.write("---\n\n")

        # --- Overall Summary ---
        f.write("## 📈 Overall Summary\n\n")
        f.write(f"| Metric                 | Value                     |\n")
        f.write(f"|--------------------------|---------------------------|\n")
        f.write(f"| **Total API Requests**   | `{metrics['total_requests']}`         |\n")
        f.write(f"| **Total Failures**       | `{metrics['total_failures']}`         |\n")
        f.write(f"| **Success Rate**         | `{metrics['success_rate_percent']:.2f}%` |\n\n")

        # --- Latency Statistics ---
        f.write("## ⏱️ API Latency Statistics (ms)\n\n")
        if not metrics['latency_stats']:
            f.write("No latency data recorded.\n\n")
        else:
            stats = metrics['latency_stats']
            f.write(f"| Statistic              | Latency (ms)              |\n")
            f.write(f"|------------------------|---------------------------|\n")
            f.write(f"| Average                | `{stats['average_ms']:.2f}`           |\n")
            f.write(f"| Median (p50)           | `{stats['p50_ms (Median)']:.2f}`           |\n")
            f.write(f"| 90th Percentile (p90)  | `{stats['p90_ms']:.2f}`           |\n")
            f.write(f"| 95th Percentile (p95)  | `{stats['p95_ms']:.2f}`           |\n")
            f.write(f"| 99th Percentile (p99)  | `{stats['p99_ms']:.2f}`           |\n")
            f.write(f"| Minimum                | `{stats['min_ms']:.2f}`           |\n")
            f.write(f"| Maximum                | `{stats['max_ms']:.2f}`           |\n\n")

        # --- HTTP Status Codes ---
        f.write("## 📊 HTTP Status Code Breakdown\n\n")
        if not metrics['status_code_distribution']:
            f.write("No status code data recorded.\n\n")
        else:
            f.write(f"| Status Code | Count | Percentage |\n")
            f.write(f"|-------------|-------|------------|\n")
            total = metrics['total_requests']
            for code, count in sorted(metrics['status_code_distribution'].items()):
                percentage = (count / total * 100) if total > 0 else 0
                f.write(f"| `{code}`      | `{count}` | `{percentage:.2f}%`  |\n")
            f.write("\n")

        # --- Critical Errors ---
        f.write("## ❗️ Critical Error Log Entries\n\n")
        if not metrics['critical_errors']:
            f.write("No critical errors recorded. Great!\n\n")
        else:
            f.write(f"Showing the first {len(metrics['critical_errors'])} recorded errors:\n\n")
            for error in metrics['critical_errors']:
                f.write("```json\n")
                f.write(json.dumps(error, indent=2))
                f.write("\n```\n\n")

    print(f"Successfully generated report: {output_file_path}")

def main():
    """
    Entry point for the report generation script.
    """
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <path_to_log_file>")
        sys.exit(1)

    log_file_path = sys.argv[1]

    # Analyze the log file
    metrics = analyze_log_file(log_file_path)

    # Determine the output file name from the run_id
    run_id = metrics.get("run_id", "report")
    output_file_path = f"{run_id}_summary.md"

    # Generate the Markdown report
    generate_markdown_report(metrics, output_file_path)

if __name__ == '__main__':
    # This allows the script to be run from the command line, for example:
    # python tests/stress_tests/generate_report.py test_run_1662194400.log
    main()
