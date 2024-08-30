This script is designed to create a comprehensive snapshot of a software project for
visibility with Large Language Model (LLM) development support with codebases. It analyzes
a specified directory, generates a detailed codemap and extracts the codebase to a single 
directory (absent any subdirectories). The tool also examines and documents imported libraries,
providing insights into the project's dependencies and produces codebases and codemaps of each 
library (default is none).

Key features include:
- List of ignored file types and directories to exclude from analysis
- Generation of hierarchical codemap showing the project structure
- Extraction of the codebase with timestamps
- Analysis and documentation of imported libraries

By capturing the essence of a project's structure, contents, and dependencies,
this tool creates a rich dataset ideal for informing LLMs to understand and work
with complex software projects. It aims to enhance an LLM's ability to comprehend
code organization, dependencies, and project architectures
