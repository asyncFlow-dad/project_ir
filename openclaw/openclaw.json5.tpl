{
  "gateway": {
    "mode": "local",
    "port": ${OPENCLAW_GATEWAY_PORT},
    "bind": "${OPENCLAW_GATEWAY_BIND}",
    "auth": {
      "mode": "token",
      "token": "${OPENCLAW_GATEWAY_TOKEN}"
    }
  },
  "session": {
    "dmScope": "per-channel-peer"
  },
  "agents": {
    "defaults": {
      "workspace": "${OPENCLAW_WORKSPACE_DIR}",
      "model": {
        "primary": "ollama/${OLLAMA_MODEL_ID}"
      },
      "sandbox": {
        "mode": "off"
      },
      "subagents": {
        "maxSpawnDepth": 1,
        "maxChildrenPerAgent": 3,
        "maxConcurrent": 4,
        "runTimeoutSeconds": 600
      }
    },
    "list": [
      {
        "id": "main",
        "identity": {
          "name": "${OPENCLAW_AGENT_NAME}",
          "theme": "${OPENCLAW_AGENT_THEME}",
          "emoji": "${OPENCLAW_AGENT_EMOJI}"
        }
      }
    ]
  },
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "${OLLAMA_BASE_URL}",
        "apiKey": "ollama-local",
        "api": "ollama",
        "models": [
          {
            "id": "${OLLAMA_MODEL_ID}",
            "name": "${OLLAMA_MODEL_NAME}",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": ${OLLAMA_CONTEXT_WINDOW},
            "maxTokens": ${OLLAMA_MAX_TOKENS}
          }
        ]
      }
    }
  },
  "tools": {
    "fs": {
      "workspaceOnly": true
    },
    "exec": {
      "security": "deny",
      "ask": "always"
    },
    "elevated": {
      "enabled": false
    }
  },
  "channels": {
    "telegram": {
      "enabled": ${TELEGRAM_ENABLED},
      "dmPolicy": "${TELEGRAM_DM_POLICY}",
      "allowFrom": ${TELEGRAM_ALLOW_FROM},
      "groupPolicy": "${TELEGRAM_GROUP_POLICY}",
      "groupAllowFrom": ${TELEGRAM_GROUP_ALLOW_FROM},
      "groups": {
        "*": {
          "requireMention": true
        }
      },
      "contextVisibility": "allowlist",
      "configWrites": false
    }
  },
  "logging": {
    "redactSensitive": "tools"
  },
  "plugins": {
    "entries": {
      "codex": {
        "enabled": true
      }
    }
  }
}
