#!/usr/bin/env python
# code to extract instructor comments from an assignment
# as written by ChatGPT with the query
# "How do I write a python script to gather all comments on an assignment in CANVAS?"
import os
import csv
import requests

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# Your institution's Canvas URL
CANVAS_URL = "https://reykjavik.instructure.com"

# Set your Canvas API token as an environment variable.
API_TOKEN = os.environ.get("CANVAS_API_TOKEN")

# Replace these with your actual IDs.
COURSE_ID = 123456
ASSIGNMENT_ID = 789012

OUTPUT_FILE = "canvas_assignment_comments.csv"


# --------------------------------------------------
# CANVAS API SETUP
# --------------------------------------------------

if not API_TOKEN:
    raise RuntimeError(
        "Missing CANVAS_API_TOKEN environment variable."
    )

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_TOKEN}"
})

BASE_URL = CANVAS_URL.rstrip("/")


# --------------------------------------------------
# FETCH ALL SUBMISSIONS
# --------------------------------------------------

def get_all_submissions():
    """Retrieve all submissions and their comments."""

    url = (
        f"{BASE_URL}/api/v1/courses/{COURSE_ID}"
        f"/assignments/{ASSIGNMENT_ID}/submissions"
    )

    params = {
        "include[]": ["submission_comments", "user"],
        "per_page": 100
    }

    submissions = []

    while url:
        response = session.get(
            url,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        submissions.extend(response.json())

        # Follow Canvas pagination links.
        url = response.links.get("next", {}).get("url")

        # Parameters are already included in the next URL.
        params = None

    return submissions


# --------------------------------------------------
# EXTRACT COMMENTS
# --------------------------------------------------

def extract_comments(submissions):
    """Convert submission comments into flat CSV rows."""

    rows = []

    for submission in submissions:
        student_id = submission.get("user_id")

        user = submission.get("user") or {}
        student_name = user.get("name", "")

        comments = submission.get("submission_comments") or []

        for comment in comments:
            rows.append({
                "course_id": COURSE_ID,
                "assignment_id": ASSIGNMENT_ID,
                "student_id": student_id,
                "student_name": student_name,
                "comment_id": comment.get("id"),
                "author_id": comment.get("author_id"),
                "author_name": comment.get("author_name", ""),
                "comment": comment.get("comment", ""),
                "created_at": comment.get("created_at", ""),
                "edited_at": comment.get("edited_at", ""),
            })

    return rows


# --------------------------------------------------
# SAVE COMMENTS TO CSV
# --------------------------------------------------

def save_to_csv(rows):
    """Write all extracted comments to a CSV file."""

    fieldnames = [
        "course_id",
        "assignment_id",
        "student_id",
        "student_name",
        "comment_id",
        "author_id",
        "author_name",
        "comment",
        "created_at",
        "edited_at",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} comments.")
    print(f"Saved to: {OUTPUT_FILE}")


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

def main():
    print("Fetching Canvas submissions...")

    submissions = get_all_submissions()

    print(f"Retrieved {len(submissions)} submissions.")

    comments = extract_comments(submissions)

    save_to_csv(comments)


if __name__ == "__main__":
    main()

