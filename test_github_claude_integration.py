import unittest
from unittest.mock import patch, MagicMock
from github_claude_integration import (
    get_repo, get_issue, get_claude_response, create_branch,
    commit_changes, apply_changes, create_pull_request,
    check_syntax, sanitize_code
)

class TestGitHubClaudeIntegration(unittest.TestCase):

    @patch('github_claude_integration.g')
    def test_get_repo(self, mock_github):
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo
        result = get_repo('owner/repo')
        self.assertEqual(result, mock_repo)

    @patch('github_claude_integration.g')
    def test_get_issue(self, mock_github):
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        result = get_issue(mock_repo, 1)
        self.assertEqual(result, mock_issue)

    @patch('github_claude_integration.requests.post')
    def test_get_claude_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'completion': 'Test response'}
        mock_post.return_value = mock_response
        result = get_claude_response('Test prompt')
        self.assertEqual(result, 'Test response')

    def test_apply_changes(self):
        original = "def function():\n    pass"
        changes = "def function():\n    return True"
        result = apply_changes(original, changes)
        self.assertEqual(result, changes)

    def test_check_syntax(self):
        valid_code = "def function():\n    return True"
        invalid_code = "def function() return True"
        self.assertTrue(check_syntax(valid_code))
        self.assertFalse(check_syntax(invalid_code))

    def test_sanitize_code(self):
        safe_code = "print('Hello, World!')"
        unsafe_code = "exec('print(\"Hello, World!\")')"
        self.assertTrue(sanitize_code(safe_code))
        self.assertFalse(sanitize_code(unsafe_code))

if __name__ == '__main__':
    unittest.main()