import os
import sys
import logging
import re
from pathlib import Path
import requests
from github import Github, GithubException
from dotenv import load_dotenv
import ast
import tempfile
import git

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize GitHub client
try:
    g = Github(os.getenv('GITHUB_TOKEN'))
except Exception as e:
    logging.error(f"Failed to initialize GitHub client: {e}")
    sys.exit(1)

def parse_github_issue_url(url):
    """Parse GitHub issue URL to extract owner, repo, and issue number."""
    pattern = r"https://github.com/([^/]+)/([^/]+)/issues/(\d+)"
    match = re.match(pattern, url)
    if match:
        return match.groups()
    raise ValueError('Invalid GitHub issue URL')

def fork_repo(repo):
    """Fork the repository."""
    try:
        user = g.get_user()
        forked_repo = user.create_fork(repo)
        logging.info(f"Repository forked successfully: {forked_repo.full_name}")
        return forked_repo
    except GithubException as e:
        logging.error(f"GitHub API error when forking repository: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when forking repository: {e}")
        raise

def clone_repo(repo, local_path):
    """Clone the repository to a local folder."""
    try:
        git.Repo.clone_from(repo.clone_url, local_path)
        logging.info(f"Repository cloned successfully to {local_path}")
        return local_path
    except git.GitCommandError as e:
        logging.error(f"Git error when cloning repository: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when cloning repository: {e}")
        raise

def index_repo(repo_path):
    """Index the repository and return a list of files."""
    try:
        file_list = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_list.append(os.path.relpath(os.path.join(root, file), repo_path))
        return file_list
    except Exception as e:
        logging.error(f"Error indexing repository: {e}")
        raise

def get_file_content(repo, file_path, ref='main'):
    """Get the content of a file from the repository."""
    try:
        content = repo.get_contents(file_path, ref=ref)
        return content.decoded_content.decode('utf-8')
    except Exception as e:
        logging.error(f"Error getting file content: {e}")
        raise

def generate_plan(issue, file_list):
    """Generate a plan for fixing the issue."""
    prompt = f"""
Given the following GitHub issue:
Title: {issue.title}
Body: {issue.body}

And the following list of files in the repository:
{', '.join(file_list)}

Please generate a plan to fix this issue. The plan should include:
1. Which files need to be modified
2. A brief description of the changes needed for each file
3. Any additional steps required to implement the fix

Provide the plan in a structured format that can be easily parsed and displayed in a web UI.
Include code snippets where appropriate, enclosed in triple backticks.
"""
    return get_ai_response(prompt)

def get_ai_response(prompt):
    """Get a response from OpenRouter API."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "anthropic/claude-3-5-sonnet-20240620",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.Timeout:
        logging.error("Timeout error when getting AI response")
        raise
    except requests.RequestException as e:
        logging.error(f"Network error when getting AI response: {e}")
        raise
    except KeyError as e:
        logging.error(f"Unexpected response format from AI API: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when getting AI response: {e}")
        raise

def create_branch(repo, branch_name, base_branch='main'):
    """Create a new branch in the repository."""
    try:
        source = repo.get_branch(base_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
        logging.info(f"Branch '{branch_name}' created successfully")
    except GithubException as e:
        logging.error(f"GitHub API error when creating branch: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when creating branch: {e}")
        raise

def commit_changes(repo, branch_name, file_path, commit_message, content):
    """Commit changes to a file in the specified branch."""
    try:
        contents = repo.get_contents(file_path, ref=branch_name)
        repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch_name)
        logging.info(f"Changes committed to '{file_path}' in branch '{branch_name}'")
    except GithubException as e:
        logging.error(f"GitHub API error when committing changes: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when committing changes: {e}")
        raise

def create_pull_request(repo, branch_name, base_branch, title, body):
    """Create a pull request."""
    try:
        pr = repo.create_pull(title=title, body=body, head=branch_name, base=base_branch)
        logging.info(f"Pull request created: {pr.html_url}")
        return pr
    except GithubException as e:
        logging.error(f"GitHub API error when creating pull request: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when creating pull request: {e}")
        raise

def check_syntax(code):
    """Check if the given code has valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def sanitize_code(code):
    """Check if the code contains potentially unsafe operations."""
    unsafe_operations = ['exec', 'eval', 'os.system', 'subprocess', '__import__', 'open']
    return all(op not in code for op in unsafe_operations)

def extract_code_snippets(text):
    """Extract code snippets from text enclosed in triple backticks."""
    pattern = r'```(?:python)?\s*(.*?)\s*```'
    return re.findall(pattern, text, re.DOTALL)

def process_github_issue(issue_url):
    try:
        owner, repo_name, issue_number = parse_github_issue_url(issue_url)
        original_repo = g.get_repo(f"{owner}/{repo_name}")
        issue = original_repo.get_issue(int(issue_number))

        # Fork the repository
        forked_repo = fork_repo(original_repo)

        # Clone the forked repository
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = clone_repo(forked_repo, temp_dir)

            # Index the repository
            file_list = index_repo(local_path)

            # Generate a plan
            plan = generate_plan(issue, file_list)

            # Check if the plan contains any code snippets
            code_snippets = extract_code_snippets(plan)
            
            # Validate syntax of code snippets
            invalid_snippets = []
            for i, snippet in enumerate(code_snippets):
                if not check_syntax(snippet):
                    invalid_snippets.append(f"Snippet {i+1}")

            if invalid_snippets:
                raise ValueError(f"The following code snippets have invalid syntax: {', '.join(invalid_snippets)}")

            # Check for potentially unsafe operations
            unsafe_snippets = []
            for i, snippet in enumerate(code_snippets):
                if not sanitize_code(snippet):
                    unsafe_snippets.append(f"Snippet {i+1}")

            if unsafe_snippets:
                raise ValueError(f"The following code snippets contain potentially unsafe operations: {', '.join(unsafe_snippets)}")

        return {
            "suggested_plan": plan
        }
    except ValueError as e:
        logging.error(f"Value error when processing GitHub issue: {e}")
        raise
    except GithubException as e:
        logging.error(f"GitHub API error when processing issue: {e}")
        raise
    except requests.RequestException as e:
        logging.error(f"Network error when processing issue: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when processing GitHub issue: {e}")
        raise

def implement_plan(issue_url):
    try:
        owner, repo_name, issue_number = parse_github_issue_url(issue_url)
        original_repo = g.get_repo(f"{owner}/{repo_name}")
        issue = original_repo.get_issue(int(issue_number))

        # Fork the repository
        forked_repo = fork_repo(original_repo)

        # Clone the forked repository
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = clone_repo(forked_repo, temp_dir)

            # Create a new branch
            branch_name = f"fix-issue-{issue_number}"
            create_branch(forked_repo, branch_name)

            # Generate and implement the plan
            file_list = index_repo(local_path)
            plan = generate_plan(issue, file_list)
            
            # Extract and validate code snippets
            code_snippets = extract_code_snippets(plan)
            for snippet in code_snippets:
                if not check_syntax(snippet) or not sanitize_code(snippet):
                    raise ValueError("Invalid or unsafe code in the implementation plan")

            # Implement the changes (this is a simplified example)
            # In a real-world scenario, you would parse the plan and make the necessary changes
            file_to_modify = "README.md"
            current_content = get_file_content(forked_repo, file_to_modify)
            new_content = current_content + f"\n\n## Fix for issue #{issue_number}\n\nThis is an automated fix for the issue."
            
            # Commit the changes
            commit_changes(forked_repo, branch_name, file_to_modify, f"Fix issue #{issue_number}", new_content)

            # Create a pull request
            pr = create_pull_request(
                original_repo,  # Create PR in the original repo
                f"{forked_repo.owner.login}:{branch_name}",  # head branch (in forked repo)
                "main",  # base branch
                f"Fix for issue #{issue_number}",
                f"This is an AI-generated fix for issue #{issue_number}\n\nOriginal issue: {issue.title}\n\nImplemented plan:\n{plan}"
            )

        return {
            "pull_request_url": pr.html_url
        }
    except ValueError as e:
        logging.error(f"Value error when implementing plan: {e}")
        raise
    except GithubException as e:
        logging.error(f"GitHub API error when implementing plan: {e}")
        raise
    except requests.RequestException as e:
        logging.error(f"Network error when implementing plan: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when implementing plan: {e}")
        raise

if __name__ == "__main__":
    # For testing purposes
    issue_url = "https://github.com/openai/openai-python/issues/645"
    try:
        result = process_github_issue(issue_url)
        print(f"Suggested plan:\n{result['suggested_plan']}")
        
        implement_result = implement_plan(issue_url)
        print(f"Pull request created: {implement_result['pull_request_url']}")
    except Exception as e:
        print(f"Error: {e}")