
# GitHub Issue Fixer

This tool automatically generates fixes for GitHub issues using AI and creates pull requests with the suggested changes.

## Prerequisites

- Python 3.7+
- GitHub account and personal access token
- OpenRouter API key

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with the following content:
   ```
   GITHUB_TOKEN=your_github_token_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Usage

1. Start the server:
   ```
   python server.py
   ```
2. Open a web browser and navigate to `http://localhost:5000`
3. Enter a GitHub issue URL in the format `https://github.com/owner/repo/issues/number`
4. Click "Generate Fix" to process the issue

The tool will:
1. Clone the repository
2. Analyze the issue
3. Generate a fix using AI (via OpenRouter)
4. Create a new branch
5. Commit the changes
6. Create a pull request with the suggested fix

## Note on OpenRouter

This tool uses OpenRouter to access AI models, which helps with rate limiting and provides more flexibility. Make sure to sign up for an OpenRouter account and obtain an API key before using this tool.

## Security Considerations

- This tool clones repositories and executes AI-generated code. Use it only with trusted repositories and review all suggested changes before merging.
- The tool includes basic code sanitization, but it's recommended to thoroughly review any generated code before running or merging it.

## Limitations

- Currently, the tool assumes the fix will be applied to a file named `main.py`. This may need to be adjusted based on the specific issue and repository structure.
- The AI-generated fixes may not always be correct or complete. Always review the suggestions before merging.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
