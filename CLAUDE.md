# K-pop Digest Project Notes

- Domain: kpopdigest.com
- Frontend: deployed on Vercel.
- Backend: running on my MacBook as a daily cron job, integrate the news search API, call an LLM to rewrite articles, and store records in the database.
- Database: Neon.

# Coding Agent Guidelines

## 1. Understand Before Coding

### Keep It Simple and Maintainable

- Explore the codebase first to understand the structure and identify reusable code.
- Before creating a new function, check whether existing code can be reused, extended, or slightly modified.
- Use the simplest solution with the minimum necessary code.

### Stay Within the Coding Task

- Consult the user before making engineering judgments involving mathematics, algorithms, or domain-specific behavior.
- Check official documentation for external APIs, libraries, frameworks, or platform behavior. 

## 2. Test-Oriented Development

- Split implementation into small, testable functions.
- Write tests for small functions that contain real logic, not trivial wrappers or pass-through code.
- Tests should verify that each function fulfills its intended purpose.
- Bug fix: write a test that reproduces the issue, then fix the code and verify the test passes.
- Refactoring: ensure relevant tests pass before and after the change.

## 3. Documentation

- Add or update descriptions for files and functions so they explain the current purpose and behavior, not the history of changes.
- Do not write author information.
- Do not repeat the current value of a parameter in comments. Explain what the parameter means.

## 4. Interaction with the User

- After coding, run linter and unit tests when possible.
- Do not run tests or simulations that require manual UI interaction like 'npm run dev'. Tell the user when such verification is needed.
- Do what you can first. Collect any required user input or actions and ask for them together.
- After completing and testing a feature or fix, remind the user to commit before moving on. Suggest a one-line commit message.
