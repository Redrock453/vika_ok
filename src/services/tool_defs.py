"""Tool definitions for LLM function calling (OpenAI-compatible)."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ssh_run",
            "description": "Execute a command on a remote server via SSH",
            "parameters": {
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "enum": ["vika-do-v2", "sitl"],
                        "description": "Target server name"
                    },
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    }
                },
                "required": ["server", "command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ssh_status",
            "description": "Get system info (OS, RAM, disk, uptime) from a remote server",
            "parameters": {
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "enum": ["vika-do-v2", "sitl"],
                    }
                },
                "required": ["server"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ssh_docker",
            "description": "List Docker containers on a remote server",
            "parameters": {
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "enum": ["vika-do-v2", "sitl"],
                    }
                },
                "required": ["server"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ssh_read_file",
            "description": "Read file contents from a remote server",
            "parameters": {
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "enum": ["vika-do-v2", "sitl"],
                    },
                    "path": {
                        "type": "string",
                        "description": "Absolute file path"
                    }
                },
                "required": ["server", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "opencode_run",
            "description": "Delegate a coding task to OpenCode AI agent. Use for writing code, fixing bugs, creating projects, refactoring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Description of the coding task"
                    },
                    "workdir": {
                        "type": "string",
                        "description": "Working directory on the server",
                        "default": "/tmp"
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web via DuckDuckGo",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Search the knowledge base (Qdrant) for relevant information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
]
