# AI-Shifu Configuration Scripts

This directory contains utility scripts for managing AI-Shifu configuration.

## generate_env_examples.py

Generates environment configuration example files from the application's configuration definitions.

### Purpose

This script automatically generates two types of `.env.example` files:

1. **`.env.example.minimal`** - Contains only the required environment variables that MUST be configured
2. **`.env.example.full`** - Contains all available environment variables with their defaults and descriptions

### Usage

From the `src/api` directory:

```bash
python scripts/generate_env_examples.py
```

### Output

The script generates two files in the `docker` directory:

- `.env.example.minimal` - Minimal configuration with only required variables
- `.env.example.full` - Complete configuration reference

### Features

- Automatically extracts configuration from `flaskr.common.config`
- Groups variables by category (Database, Redis, Auth, LLM, etc.)
- Includes descriptions, types, and validation information
- Marks required variables clearly
- Handles multi-line descriptions
- Protects secret values by not including defaults
- Provides a summary of configuration requirements

### When to Use

Run this script:

- After adding new environment variables to `config.py`
- When updating variable descriptions or requirements
- To generate fresh example files for documentation
- When onboarding new developers who need configuration templates

### Example Output

The script provides helpful output:

```
✅ Generated minimal configuration: .env.example.minimal
✅ Generated full configuration: .env.example.full

📊 Summary:
  - Total variables: 106
  - Required variables: 3
  - Optional variables: 103

📌 Required variables that must be configured:
  [AUTH]
    - SECRET_KEY
    - UNIVERSAL_VERIFICATION_CODE
  [DATABASE]
    - SQLALCHEMY_DATABASE_URI
```

### Configuration Workflow

1. Run the generation script
2. Copy the appropriate example file:
   - For minimal setup: `cp .env.example.minimal .env`
   - For full control: `cp .env.example.full .env`
3. Edit `.env` and configure all required variables
4. Never commit `.env` to version control
