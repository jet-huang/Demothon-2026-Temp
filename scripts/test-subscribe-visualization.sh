#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test the subscription endpoint
echo -e "${BLUE}Testing subscription endpoint...${NC}"
response=$(curl -s -X POST \
  http://localhost:8000/api/v1/visualization/subscribe \
  -H "Content-Type: application/json" \
  -d '{"subscription_targets":[{"type":"my_a2a_messages"}]}')

# Extract key fields
stream_id=$(echo "$response" | jq -r '.stream_id')
sse_endpoint_url=$(echo "$response" | jq -r '.sse_endpoint_url')
status=$(echo "$response" | jq -r '.actual_subscribed_targets[0].status')

echo ""
echo -e "${GREEN}Response received:${NC}"
echo -e "  ${CYAN}Stream ID:${NC} $stream_id"
echo -e "  ${CYAN}SSE Endpoint:${NC} $sse_endpoint_url"
echo -e "  ${CYAN}Status:${NC} $status"
echo ""

# Check if subscription was successful
if [ "$status" = "subscribed" ]; then
  echo -e "${GREEN}✓ Subscription successful${NC}"
  echo ""
  read -p "Would you like to subscribe to the SSE endpoint? (y/n): " choice
  
  if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    echo ""
    echo -e "${BLUE}Subscribing to SSE stream (press Ctrl+C to stop)...${NC}"
    echo "---"
    
    # Stream and format SSE events
    curl -s -N -H "Accept: text/event-stream" "$sse_endpoint_url" | while IFS= read -r line; do
      # Check for connection message
      if [[ "$line" == *"SSE connection established"* ]]; then
        echo -e "${GREEN}$line${NC}"
        echo ""
        continue
      fi
      
      # Parse event type
      if [[ "$line" == event:* ]]; then
        event_type="${line#event: }"
        echo -e "${YELLOW}[EVENT: $event_type]${NC}"
        continue
      fi
      
      # Parse and format data
      if [[ "$line" == data:* ]]; then
        data="${line#data: }"
        
        # Extract key fields for display
        timestamp=$(echo "$data" | jq -r '.timestamp // empty' 2>/dev/null)
        source=$(echo "$data" | jq -r '.source_entity // empty' 2>/dev/null)
        target=$(echo "$data" | jq -r '.target_entity // empty' 2>/dev/null)
        direction=$(echo "$data" | jq -r '.direction // empty' 2>/dev/null)
        message=$(echo "$data" | jq -r '.payload_summary.params_preview // .message // empty' 2>/dev/null | head -c 320)
        
        echo -e "  ${CYAN}Time:${NC} $timestamp"
        echo -e "  ${CYAN}Direction:${NC} $direction"
        echo -e "  ${CYAN}From:${NC} $source → ${CYAN}To:${NC} $target"
        
        if [ ! -z "$message" ]; then
          echo -e "  ${CYAN}Preview:${NC} ${message}..."
        fi
        
        # Optional: Show full payload in compact JSON
        # echo -e "  ${CYAN}Full Data:${NC}"
        # echo "$data" | jq -c '.' 2>/dev/null | sed 's/^/    /'
        
        echo ""
        continue
      fi
      
      # Empty lines separate events
      if [ -z "$line" ]; then
        continue
      fi
    done
  fi
else
  echo -e "${RED}✗ Subscription failed${NC}"
  exit 1
fi
