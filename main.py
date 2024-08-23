from github_claude_integration import process_github_issue, implement_plan

def fix_issue(issue_url):
    """
    This function attempts to fix a GitHub issue.
    
    Args:
        issue_url (str): The URL of the GitHub issue to fix.
    
    Returns:
        dict: A dictionary containing the result of the fix attempt.
    """
    try:
        # First, process the issue to generate a plan
        plan_result = process_github_issue(issue_url)
        print(f"Generated plan: {plan_result['suggested_plan']}")
        
        # Then, implement the plan
        implementation_result = implement_plan(issue_url)
        print(f"Pull request created: {implementation_result['pull_request_url']}")
        
        return {
            "success": True,
            "plan": plan_result['suggested_plan'],
            "pull_request_url": implementation_result['pull_request_url']
        }
    except Exception as e:
        print(f"Error fixing issue: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Example usage
    issue_url = "https://github.com/example/repo/issues/1"
    result = fix_issue(issue_url)
    print(f"Fix attempt result: {result}")
