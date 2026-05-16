#!/bin/bash

  # Parse command-line arguments
  FILTER_STREAMING=false
  POSITIONAL_ARGS=()

  while [[ $# -gt 0 ]]; do
    case $1 in
      -f|--filter-streaming)
        FILTER_STREAMING=true
        shift
        ;;
      *)
        POSITIONAL_ARGS+=("$1")
        shift
        ;;
    esac
  done

  # Restore positional parameters
  set -- "${POSITIONAL_ARGS[@]}"

  IMAGE_FILE="$1"
  QUESTION="${2:-請幫我分析這份圖檔}"
  AGENT_NAME="${3:-OrchestratorAgent}"
  API_URL="${API_URL:-http://localhost:8000}"

  if [ ! -f "$IMAGE_FILE" ]; then
      echo "Error: File not found: $IMAGE_FILE"
      echo ""
      echo "Usage: $0 [-f|--filter-streaming] <image_file> [question] [agent_name]"
      echo "  -f, --filter-streaming    Filter out streaming/intermediate responses"
      exit 1
  fi

  # Get filename and detect mime type
  FILENAME=$(basename "$IMAGE_FILE")
  MIME_TYPE=$(file -b --mime-type "$IMAGE_FILE")

  echo "📤 Sending file: $FILENAME ($MIME_TYPE)"
  echo "💬 Question: $QUESTION"
  echo "🤖 Agent: $AGENT_NAME"
  if [[ "$FILTER_STREAMING" == "true" ]]; then
      echo "🔍 Filter: Streaming responses will be hidden"
  fi
  echo ""

  # Encode to base64 (remove line breaks)
  if [[ "$OSTYPE" == "darwin"* ]]; then
      BASE64_CONTENT=$(base64 -i "$IMAGE_FILE")
  else
      BASE64_CONTENT=$(base64 -w 0 "$IMAGE_FILE")
  fi

  # Generate unique IDs
  REQ_ID="req-$(date +%s)"
  MSG_ID="msg-$(date +%s)"

  # Build JSON and send
  echo "🔄 Submitting task..."
  
  # Create a temporary file for the JSON payload to avoid "Argument list too long" error
  TEMP_JSON=$(mktemp)
  trap "rm -f $TEMP_JSON" EXIT
  
  # Build JSON using a here-document to handle large base64 content
  cat > "$TEMP_JSON" <<EOF
{
  "jsonrpc": "2.0",
  "id": "$REQ_ID",
  "method": "message/stream",
  "params": {
    "message": {
      "role": "user",
      "messageId": "$MSG_ID",
      "kind": "message",
      "parts": [
        {
          "kind": "text",
          "text": "$QUESTION"
        },
        {
          "kind": "file",
          "file": {
            "bytes": "$BASE64_CONTENT",
            "name": "$FILENAME",
            "mimeType": "$MIME_TYPE"
          }
        }
      ],
      "metadata": {
        "agent_name": "$AGENT_NAME"
      }
    }
  }
}
EOF

  RESPONSE=$(curl -s -X POST "$API_URL/api/v1/message:stream" \
         -H 'Content-Type: application/json' \
         -d @"$TEMP_JSON")

  # Check if request was successful
  if [ $? -ne 0 ] || [ -z "$RESPONSE" ]; then
      echo "❌ Error: Failed to send request"
      exit 1
  fi

  # Pretty print the response
  echo "✅ Task submitted successfully!"
  echo ""
  echo "Response:"
  echo "$RESPONSE" | jq '.'

  # Extract task ID and context ID
  TASK_ID=$(echo "$RESPONSE" | jq -r '.result.id')
  CONTEXT_ID=$(echo "$RESPONSE" | jq -r '.result.contextId')

  if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
      echo ""
      echo "❌ Error: Could not extract task ID from response"
      exit 1
  fi

  echo ""
  echo "📋 Task ID: $TASK_ID"
  echo "🔗 Context ID: $CONTEXT_ID"
  echo ""

  # Ask user if they want to subscribe to SSE
  read -p "📡 Do you want to subscribe to SSE events? (y/n): " -n 1 -r
  echo ""

  if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo ""
      echo "🔌 Connecting to SSE stream..."
      echo "   URL: $API_URL/api/v1/sse/subscribe/$TASK_ID"
      echo "   (Press Ctrl+C to stop)"
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""

      # Subscribe to SSE with pretty printing
      curl -N "$API_URL/api/v1/sse/subscribe/$TASK_ID" 2>/dev/null | {
          CURRENT_EVENT=""
          EVENT_HEADER=""
          while IFS= read -r line; do
              # Check if line is an event type
              if [[ $line == event:* ]]; then
                  CURRENT_EVENT=$(echo "$line" | sed 's/^event: //')
                  # Buffer the event header instead of printing immediately
                  case $CURRENT_EVENT in
                      "status_update")
                          EVENT_HEADER="📊 Status Update:"
                          ;;
                      "artifact_update")
                          EVENT_HEADER="📎 Artifact Update:"
                          ;;
                      "final_response")
                          EVENT_HEADER="✅ Final Response:"
                          ;;
                      "error")
                          EVENT_HEADER="❌ Error:"
                          ;;
                      *)
                          EVENT_HEADER="📨 Event: $CURRENT_EVENT"
                          ;;
                  esac
              # Check if line is data
              elif [[ $line == data:* ]]; then
                  DATA=$(echo "$line" | sed 's/^data: //')
                  # Pretty print JSON if possible
                  if echo "$DATA" | jq '.' >/dev/null 2>&1; then
                      # Check if we should filter this message
                      SHOULD_FILTER=false
                      if [[ "$FILTER_STREAMING" == "true" ]]; then
                          IS_FINAL=$(echo "$DATA" | jq -r '.result.final' 2>/dev/null)
                          STATUS_STATE=$(echo "$DATA" | jq -r '.result.status.state' 2>/dev/null)
                          HAS_DATA_PARTS=$(echo "$DATA" | jq -r '.result.status.message.parts[]? | select(.kind == "data") | .kind' 2>/dev/null)
                          # Filter streaming chunks: final=false, state=working, AND no data parts
                          if [[ "$IS_FINAL" == "false" ]] && [[ "$STATUS_STATE" == "working" ]] && [[ -z "$HAS_DATA_PARTS" ]]; then
                              SHOULD_FILTER=true
                          fi
                      fi

                      # Display the message if not filtered
                      if [[ "$SHOULD_FILTER" == "false" ]]; then
                          # Print buffered event header if available
                          if [[ -n "$EVENT_HEADER" ]]; then
                              echo "$EVENT_HEADER"
                              EVENT_HEADER=""
                          fi
                          echo "$DATA" | jq '.'

                          # Extract and beautify the text if status is completed
                          STATUS_STATE=$(echo "$DATA" | jq -r '.result.status.state // empty' 2>/dev/null)
                          if [[ "$STATUS_STATE" == "completed" ]]; then
                              RESPONSE_TEXT=$(echo "$DATA" | jq -r '.result.status.message.parts[]? | select(.kind == "text") | .text' 2>/dev/null)
                              if [ -n "$RESPONSE_TEXT" ] && [ "$RESPONSE_TEXT" != "null" ]; then
                                  echo ""
                                  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                                  echo "💬 Beautified Response:"
                                  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                                  echo ""
                                  echo "$RESPONSE_TEXT"
                                  echo ""
                                  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                              fi
                          fi
                          echo ""
                      else
                          # Clear buffered event header since we're filtering this message
                          EVENT_HEADER=""
                      fi
                  else
                      # For non-JSON data, also apply filtering if enabled
                      SHOULD_FILTER_NON_JSON=false
                      if [[ "$FILTER_STREAMING" == "true" ]] && [[ -z "$DATA" || "$DATA" == "" ]]; then
                          SHOULD_FILTER_NON_JSON=true
                          EVENT_HEADER=""
                      fi

                      if [[ "$SHOULD_FILTER_NON_JSON" == "false" ]]; then
                          if [[ -n "$EVENT_HEADER" ]]; then
                              echo "$EVENT_HEADER"
                              EVENT_HEADER=""
                          fi
                          echo "$DATA"
                          echo ""
                      fi
                  fi
              # Just print other lines (comments, blank lines)
              else
                  # Skip empty/whitespace lines when filtering is enabled
                  if [[ "$FILTER_STREAMING" == "true" ]]; then
                      # Skip all empty or whitespace-only lines
                      if [[ -n "$line" && -n "${line//[[:space:]]/}" ]]; then
                          echo "$line"
                      fi
                  else
                      [[ -n "$line" ]] && echo "$line"
                  fi
              fi
          done
      }

      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "🏁 Stream ended"
  else
      echo ""
      echo "ℹ️  To subscribe later, run:"
      echo "   curl -N '$API_URL/api/v1/sse/subscribe/$TASK_ID'"
      echo ""
  fi
