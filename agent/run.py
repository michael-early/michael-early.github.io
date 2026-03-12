import os
import sys


def main():
    issue_number = os.environ.get("ISSUE_NUMBER", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")

    print(f"Issue #{issue_number}: {issue_title}")
    print(f"Body:\n{issue_body}")
    print("Agent stub complete — no API calls in Phase 1")

    sys.exit(0)


if __name__ == "__main__":
    main()
