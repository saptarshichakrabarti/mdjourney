# Husky Setup Instructions

This project uses Husky and lint-staged to automatically run linting and formatting on staged files before commits.

## Initial Setup

After cloning the repository, run these commands to set up the Git hooks:

```bash
cd frontend

# Install dependencies (this installs husky and lint-staged)
npm install

# Initialize Husky
npx husky init

# Create the pre-commit hook
npx husky add .husky/pre-commit "npx lint-staged"
```

## What It Does

When you run `git commit`, Husky will automatically:

1. Run ESLint with auto-fix on staged JavaScript/TypeScript files
2. Run Prettier to format all staged files
3. If there are unfixable errors, the commit will be aborted
4. If everything passes, the commit proceeds

## Manually Running Linters

You can also run the linters manually:

```bash
# Run ESLint
npm run lint

# Run Prettier (format files)
npx prettier --write .

# Run TypeScript compiler check
npm run build
```

